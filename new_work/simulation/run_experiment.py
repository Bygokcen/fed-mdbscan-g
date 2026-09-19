"""
Main experiment runner for Fed-MDBSCAN simulation.

Orchestrates the full federated learning experiment:
    1. Load and distribute data across IoT clients
    2. Run multiple communication rounds
    3. Compare Fed-MDBSCAN against baseline methods
    4. Collect metrics and generate visualizations

Usage:
    python -m simulation.run_experiment
    python -m simulation.run_experiment --dataset mnist --num_clients 20 --num_rounds 10
"""

import os
import sys
import json
import time
import argparse
import hashlib
import platform
import resource
from pathlib import Path
import numpy as np
import torch

from simulation.data_distributor import (
    load_dataset, distribute_iid, distribute_non_iid,
    create_client_loaders,
    apply_data_size_variance, extract_root_subset, repair_minimum_partition,
    get_client_class_distribution,
)
from simulation.models import get_model, get_model_weights
from simulation.client import Client
from simulation.server import Server
from simulation.metrics import (
    MetricsCollector, evaluate_attack_alert, evaluate_detection_decision,
)
from simulation.contracts import (canonical_json, resolve_experiment_config,
    build_participation_schedule, derive_seed)
from simulation.visualize import generate_all_plots
from torch.utils.data import DataLoader


def _num_classes_for_dataset(dataset_name):
    """Return class count needed by data-level attacks such as label flip."""
    if dataset_name == 'har':
        return 6
    return 10


def _update_array_digest(digest, name, value):
    if torch.is_tensor(value):
        array = value.detach().cpu().numpy()
    else:
        array = np.asarray(value)
    contiguous = np.ascontiguousarray(array)
    digest.update(name.encode('utf-8') + b'\0')
    digest.update(str(contiguous.dtype).encode('ascii') + b'\0')
    digest.update(canonical_json(list(contiguous.shape)).encode('utf-8') + b'\0')
    digest.update(contiguous.tobytes())


def _dataset_identity(dataset):
    """Fingerprint raw examples, labels, transforms, and dataset implementation."""
    digest = hashlib.sha256()
    metadata = {
        'class': f'{type(dataset).__module__}.{type(dataset).__qualname__}',
        'length': len(dataset),
        'transform': str(getattr(dataset, 'transform', None)),
        'target_transform': str(getattr(dataset, 'target_transform', None)),
    }
    digest.update(canonical_json(metadata).encode('utf-8'))
    found = False
    for name in ('data', 'targets', 'X', 'y'):
        if hasattr(dataset, name):
            _update_array_digest(digest, name, getattr(dataset, name))
            found = True
    if not found:
        raise ValueError('dataset does not expose hashable raw data and labels')
    metadata['sha256'] = digest.hexdigest()
    return metadata


def _model_identity(model):
    architecture = {
        'class': f'{type(model).__module__}.{type(model).__qualname__}',
        'repr': str(model),
        'parameters': [
            {'name': name, 'shape': list(param.shape), 'dtype': str(param.dtype)}
            for name, param in model.named_parameters()
        ],
    }
    architecture['sha256'] = hashlib.sha256(
        canonical_json(architecture).encode('utf-8')
    ).hexdigest()
    return architecture


def _validated_output_path(output_dir):
    project_root = Path(__file__).resolve().parents[2]
    target = Path(output_dir).resolve()
    for relative in (
        'new_work/results/heterogeneous_v3_mnist',
        'new_work/results/heterogeneous_v3_fashion_mnist',
        'new_work/results/heterogeneous_v3_har',
        'new_work/results/phase2b_report',
    ):
        try:
            target.relative_to((project_root / relative).resolve())
        except ValueError:
            continue
        raise ValueError('validated output cannot be inside a legacy result root')
    results_root = (project_root / 'new_work/results').resolve()
    validated_root = (results_root / 'validated/audit-v2').resolve()
    try:
        target.relative_to(results_root)
    except ValueError:
        pass
    else:
        try:
            target.relative_to(validated_root)
        except ValueError as exc:
            raise ValueError(
                'new_work/results outputs must use results/validated/audit-v2',
            ) from exc
    return str(target)


def run_single_experiment(config, method, seed=42):
    """
    Run a single FL experiment with a specific aggregation method.

    Args:
        config: experiment configuration dict
        method: aggregation method name
        seed: random seed

    Returns:
        metrics_collector: MetricsCollector with logged results
    """
    started_at = time.time()
    config = resolve_experiment_config({**config, 'seed': seed})

    # Set seeds for reproducibility
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n{'='*60}")
    print(f"  Method: {method} | Device: {device}")
    print(f"  Clients: {config['num_clients']} | Rounds: {config['num_rounds']}")
    print(f"  Dataset: {config['dataset']} | Malicious: {config['malicious_ratio']*100:.0f}%")
    print(f"{'='*60}")

    # Load dataset
    train_dataset, test_dataset = load_dataset(
        config['dataset'], data_dir=config['data_dir'],
    )
    test_loader = DataLoader(
        test_dataset, batch_size=config['test_batch_size'], shuffle=False,
    )
    num_classes = config['num_classes']

    # Distribute data across clients (Non-IID)
    if config['iid']:
        client_indices = distribute_iid(
            train_dataset, config['num_clients'], seed=seed
        )
    else:
        client_indices = distribute_non_iid(
            train_dataset, config['num_clients'],
            alpha=config['non_iid_alpha'], seed=seed
        )

    # Apply realistic per-device data size variance (Faz 1.2 — heterojen IoT)
    data_size_sigma = config['data_size_sigma']
    if data_size_sigma > 0:
        client_indices = apply_data_size_variance(
            client_indices,
            sigma=data_size_sigma,
            min_samples=config['min_samples_per_client'],
            seed=seed,
            empty_client_policy=config['empty_client_policy'],
        )

    # Always hold out a small clean root subset (FLTrust). Performed for every
    # method so that per-seed client data stays identical across methods.
    root_size = config['root_size']
    held_out_indices, client_indices = extract_root_subset(
        client_indices, size=root_size, seed=seed + 7777
    )

    before_histograms = get_client_class_distribution(train_dataset, client_indices)
    before_counts = {str(cid): len(values) for cid, values in client_indices.items()}
    moved_samples = 0
    if config['partition_policy'] == 'repair_minimum':
        client_indices, moved_samples = repair_minimum_partition(
            client_indices, config['min_samples_per_client'],
            derive_seed(seed, 'partition_repair'),
        )
    final_histograms = get_client_class_distribution(train_dataset, client_indices)
    nonempty = sorted(cid for cid, values in client_indices.items() if values)
    ordered_size = sorted(nonempty, key=lambda cid: (len(client_indices[cid]), cid))
    size_groups = {cid: min(3, rank * 4 // len(ordered_size))
                   for rank, cid in enumerate(ordered_size)}
    client_metadata = {
        str(cid): {'sample_count': len(client_indices[cid]),
                   'class_histogram': {str(k): v for k, v in final_histograms[cid].items()},
                   'size_quartile': size_groups[cid],
                   'dominant_label': int(max(final_histograms[cid], key=lambda k: (final_histograms[cid][k], -k)))}
        for cid in nonempty
    }
    client_loaders = create_client_loaders(
        train_dataset, client_indices,
        batch_size=config['batch_size'],
    )

    # Root loader only built for methods that consume it (currently FLTrust).
    if method in ('fltrust', 'fltrust_normalized') and len(held_out_indices) > 0:
        from torch.utils.data import Subset
        root_subset = Subset(train_dataset, held_out_indices)
        root_loader = DataLoader(
            root_subset, batch_size=config['root_batch_size'], shuffle=True,
        )
    else:
        root_loader = None

    latent_ids, participation_schedule = build_participation_schedule(config, nonempty)
    malicious_ids = set(latent_ids)
    schedule_hash = hashlib.sha256(canonical_json(participation_schedule).encode('utf-8')).hexdigest()

    # Create model factory
    def model_fn():
        return get_model(config['dataset'], device='cpu')

    # Create clients
    clients = []
    for cid in range(config['num_clients']):
        loader = client_loaders.get(cid)
        if loader is None:
            continue
        is_mal = cid in malicious_ids
        client = Client(
            client_id=cid,
            data_loader=loader,
            model_fn=model_fn,
            device=device,
            is_malicious=is_mal,
            attack_type=config['attack_type'],
            attack_params={
                'gaussian_std': config['gaussian_std'],
                'stealth_rho': config['stealth_rho'],
                'adaptive_alpha': config['adaptive_alpha'],
                'dataset': config['dataset'],
                'backdoor_target': config['backdoor_target'],
                'backdoor_fraction': config['backdoor_fraction'],
                'backdoor_patch_size': config['backdoor_patch_size'],
            },
        )
        clients.append(client)

    # Create server
    with torch.random.fork_rng():
        torch.manual_seed(derive_seed(seed, 'global_initialization'))
        global_model = get_model(config['dataset'], device=device)
    partition_payload = {
        'clients': {str(cid): list(indices) for cid, indices in sorted(client_indices.items())},
        'held_out': list(held_out_indices),
    }
    partition_hash = hashlib.sha256(
        canonical_json(partition_payload).encode('utf-8')
    ).hexdigest()
    initial_model_hash = hashlib.sha256(
        np.ascontiguousarray(get_model_weights(global_model)).tobytes()
    ).hexdigest()

    # Get method-specific parameters
    method_params = config['method_params'][method]

    server = Server(
        model=global_model,
        test_loader=test_loader,
        device=device,
        aggregation_method=method,
        method_params=method_params,
        root_loader=root_loader,
        root_model_fn=model_fn if root_loader is not None else None,
        aggregation_operator=config['aggregation_operator'],
        fallback_policy=config['fallback_policy'],
    )

    # Metrics collector
    metrics = MetricsCollector()
    metrics.run_metadata = {
        'dataset_identity': {
            'name': config['dataset'],
            'train': _dataset_identity(train_dataset),
            'test': _dataset_identity(test_dataset),
        },
        'partition_sha256': partition_hash,
        'schedule_sha256': schedule_hash,
        'latent_malicious_ids': latent_ids,
        'active_client_ids': nonempty,
        'participation_schedule': participation_schedule,
        'client_metadata': client_metadata,
        'partition_repair': {
            'policy': config['partition_policy'], 'moved_samples': moved_samples,
            'before_counts': before_counts,
            'before_class_histograms': {str(cid): {str(k): v for k, v in hist.items()}
                                        for cid, hist in before_histograms.items()},
            'after_counts': {str(cid): len(v) for cid, v in client_indices.items()},
        },
        'initial_model_sha256': initial_model_hash,
        'model_identity': _model_identity(global_model),
        'command': list(sys.argv),
        'start_time_unix': started_at,
        'runtime': {
            'python': platform.python_version(),
            'device': str(device),
        },
        'resolved_config': config,
    }

    # Initial evaluation
    initial_acc = server.evaluate()
    accuracy = initial_acc
    print(f"  Initial accuracy: {initial_acc:.4f}")

    by_id = {client.client_id: client for client in clients}
    for round_num in range(config['num_rounds']):
        round_start = time.time()
        scheduled_ids = participation_schedule[round_num]
        window_active = (round_num >= config['attack_start_round'] and
                         (config['attack_end_round'] is None or round_num < config['attack_end_round']))
        actual_malicious_ids = malicious_ids if window_active and config['attack_mode'] != 'clean' else set()
        # Oracle is an evaluator-only preselection: the production server never sees labels.
        oracle_excluded = actual_malicious_ids if config['attack_mode'] == 'oracle' else set()
        participating_clients = [by_id[cid] for cid in scheduled_ids if cid not in oracle_excluded]
        for client in participating_clients:
            client.is_malicious = client.client_id in actual_malicious_ids
            client.attack_params['rng'] = np.random.default_rng(
                derive_seed(seed, 'attack', round_num, client.client_id))

        if not participating_clients:
            accuracy = server.evaluate()
            round_time = time.time() - round_start
            metrics.log_round(
                round_num=round_num,
                method=method,
                accuracy=accuracy,
                fpr=0.0,
                tpr=0.0,
                time_elapsed=0.0,
                extra={
                    'round_total_time': round_time,
                    'skipped_round': 1,
                    'fallback_applied': 1,
                    'fallback_reason': 'empty_participating_cohort',
                    'degraded': 1,
                    'participant_ids': [],
                    'update_ids': [],
                    'accepted_ids': [],
                    'rejected_ids': [],
                },
            )
            continue

        # Each client trains locally and sends gradient update
        global_weights = server.get_global_weights()
        client_gradients = []
        participating_ids = []
        sample_counts = []
        attack_diagnostics = {}
        optimizer_steps = {}

        for client in participating_clients:
            gradient = client.train(
                global_weights,
                epochs=config['local_epochs'],
                lr=config['lr'],
                num_classes=num_classes,
                optimizer_momentum=config['optimizer_momentum'],
                max_local_steps=config['max_local_steps'],
                rng_seed=derive_seed(seed, 'client_training', round_num, client.client_id),
            )
            optimizer_steps[str(client.client_id)] = client.last_optimizer_steps
            if client.is_malicious:
                attack_diagnostics[str(client.client_id)] = dict(client.last_attack_diagnostics)
            client_gradients.append(gradient)
            participating_ids.append(client.client_id)
            sample_counts.append(client.get_data_size())

        if (config['attack_type'] in ('minmax_omniscient', 'minsum_omniscient',
                                      'minmax_flat_omniscient')
                and actual_malicious_ids and config['attack_mode'] != 'oracle'):
            references = np.asarray([g for cid, g in zip(participating_ids, client_gradients)
                                     if cid not in actual_malicious_ids])
            if config['attack_type'] == 'minmax_flat_omniscient':
                from simulation.audit_attacks import profile_constrained_poison
                poisoned, diag = profile_constrained_poison(
                    references, config['coordinated_profile_ratio'])
            else:
                from simulation.audit_attacks import constrained_poison
                poisoned, diag = constrained_poison(references, config['attack_type'])
            for idx, cid in enumerate(participating_ids):
                if cid in actual_malicious_ids:
                    client_gradients[idx] = poisoned.copy()
                    attack_diagnostics[str(cid)] = {'attack_type': config['attack_type'], **diag}

        # Independent server stream includes root training and server-side noise.
        server.noise_rng = np.random.default_rng(derive_seed(seed, 'server_noise', round_num))
        with torch.random.fork_rng():
            torch.manual_seed(derive_seed(seed, 'root_training', round_num))
            result = server.aggregate(
                client_gradients, participating_ids=participating_ids,
                sample_counts=sample_counts,
                update_ids=[f"{round_num}:{cid}" for cid in participating_ids],
                round_id=round_num,
            )
        server_input_ids = list(participating_ids)
        if oracle_excluded:
            # The evaluator's oracle decision covers the original scheduled cohort.
            result['decision']['rejected_ids'] = sorted(
                result['decision']['rejected_ids'] + list(oracle_excluded))
            result['decision']['update_ids'] = [f"{round_num}:{cid}" for cid in scheduled_ids]
            result['n_anomaly'] += len(oracle_excluded)
            participating_ids = list(scheduled_ids)
        detection = evaluate_detection_decision(result['decision'], actual_malicious_ids)
        alert_quality = evaluate_attack_alert(
            result['decision'], actual_malicious_ids, result.get('attack_alert', False))
        group_counts = {}
        rejected = set(result['decision']['rejected_ids'])
        for cid in participating_ids:
            if cid in actual_malicious_ids:
                continue
            meta = client_metadata[str(cid)]
            for key in ('size_quartile', 'dominant_label'):
                name = f"{key}:{meta[key]}"
                counts = group_counts.setdefault(name, {'fp': 0, 'tn': 0})
                counts['fp' if cid in rejected else 'tn'] += 1

        # Evaluate
        accuracy = server.evaluate()
        backdoor_metrics = {}
        if config['attack_type'] == 'patch_backdoor':
            from simulation.audit_attacks import stamp_trigger
            target = config['backdoor_target']
            hits = total_triggered = 0
            with torch.no_grad():
                for samples, labels in test_loader:
                    eligible = labels != target
                    if not eligible.any():
                        continue
                    samples = stamp_trigger(samples[eligible].to(device), config['dataset'], config['backdoor_patch_size'])
                    hits += int((server.model(samples).argmax(1) == target).sum())
                    total_triggered += len(samples)
            backdoor_metrics = {'backdoor_asr': hits / total_triggered if total_triggered else None,
                                'backdoor_target_hits': hits, 'backdoor_test_count': total_triggered}
        round_time = time.time() - round_start

        # Log metrics
        filter_info = result.get('filter_info', {})
        metrics.log_round(
            round_num=round_num,
            method=method,
            accuracy=accuracy,
            fpr=detection['fpr'],
            tpr=detection['tpr'],
            time_elapsed=result['filter_time'],
            extra={
                **backdoor_metrics,
                'tp': detection['tp'], 'fp': detection['fp'],
                'tn': detection['tn'], 'fn': detection['fn'],
                'n_total': config['num_clients'], 'n_active': len(nonempty),
                'n_scheduled': len(scheduled_ids), 'n_participants': len(participating_ids),
                'n_malicious': len(set(participating_ids) & actual_malicious_ids),
                'effective_malicious_ratio': len(set(participating_ids) & actual_malicious_ids) / len(participating_ids),
                'honest_majority': int(2 * len(set(participating_ids) & actual_malicious_ids) < len(participating_ids)),
                'attack_active': int(bool(actual_malicious_ids)),
                'actual_malicious_ids': sorted(actual_malicious_ids),
                'latent_malicious_ids': latent_ids,
                'scheduled_ids': scheduled_ids,
                'oracle_excluded_ids': sorted(oracle_excluded),
                'server_input_ids': server_input_ids,
                'attack_diagnostics': attack_diagnostics,
                'optimizer_steps': optimizer_steps,
                # Update geometry per participant. Recorded so that the local
                # step count, the resulting update magnitude and the accept or
                # reject decision can be analysed together after the run.
                'update_norms': result.get('update_norms', {}),
                'l0_distances': result.get('l0_distances', {}),
                'group_confusion': group_counts,
                'balanced_accuracy': server.last_class_metrics['balanced_accuracy'],
                'per_class_accuracy': server.last_class_metrics['per_class_accuracy'],
                'class_support': server.last_class_metrics['class_support'],
                'aggregation_time': result['aggregation_time'],
                'root_training_time': result['root_training_time'],
                'server_total_time': result['server_total_time'],
                'n_benign': result['n_benign'],
                'n_anomaly': result['n_anomaly'],
                'round_total_time': round_time,
                # xAI attack-alert signal (only non-trivial for fed_mdbscan_g)
                'attack_alert': int(result.get('attack_alert', False)),
                'density_gap_detected': int(result.get('density_gap_detected', False)),
                'attack_gate': int(result.get('attack_gate', False)),
                'gap_concentration': float(result.get('gap_concentration', 0.0)),
                'layer_used': result.get('layer_used', 'n/a'),
                'gate_reason': result.get('gate_reason', 'n/a'),
                'l0_rejected_count': int(filter_info.get('l0_rejected_count', 0)),
                'l2_rejected_count': int(filter_info.get('l2_rejected_count', 0)),
                'low_density_count': int(filter_info.get('low_density_count', 0)),
                'natural_clusters_count': int(
                    filter_info.get('natural_clusters_count', 0)),
                'rejected_snnc_clusters': int(
                    filter_info.get('rejected_snnc_clusters', 0)),
                'alert_tp': alert_quality['alert_tp'],
                'alert_fp': alert_quality['alert_fp'],
                'alert_fn': alert_quality['alert_fn'],
                'alert_tn': alert_quality['alert_tn'],
                'fallback_applied': int(filter_info.get('fallback_applied', False)),
                'fallback_reason': filter_info.get('fallback_reason', 'none'),
                'degraded': int(filter_info.get('degraded', False)),
                'participant_ids': list(participating_ids),
                'update_ids': list(result['decision']['update_ids']),
                'accepted_ids': list(result['decision']['accepted_ids']),
                'rejected_ids': list(result['decision']['rejected_ids']),
            }
        )

        # Print progress
        if (round_num + 1) % max(1, config['num_rounds'] // 10) == 0 or round_num == 0:
            alert_mark = '🚨' if result.get('attack_alert') else '  '
            print(f"  Round {round_num+1}/{config['num_rounds']}: "
                  f"Acc={accuracy:.4f} | FPR={detection['fpr']:.4f} | "
                  f"TPR={detection['tpr']:.4f} | "
                  f"Benign={result['n_benign']} Anomaly={result['n_anomaly']} | "
                  f"{alert_mark}Alert={result.get('attack_alert', False)} "
                  f"GC={result.get('gap_concentration', 0.0):6.1f} "
                  f"L={result.get('layer_used', 'n/a')} | "
                  f"Filter={result['filter_time']:.4f}s")


    # Final summary
    summary = metrics.get_summary(method)
    print(f"\n  Final Accuracy: {accuracy:.4f}")
    print(f"  Avg FPR: {summary.get('fpr_mean', 0):.4f}")
    print(f"  Avg Filter Time: {summary.get('time_elapsed_mean', 0):.4f}s")

    metrics.run_metadata['end_time_unix'] = time.time()
    peak_raw = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    metrics.run_metadata['peak_memory_kib'] = (
        peak_raw / 1024.0 if sys.platform == 'darwin' else peak_raw
    )
    metrics.run_metadata['exit_status'] = 0
    return metrics


def run_comparison_experiment(config):
    """
    Run the full comparison experiment across all methods.

    Args:
        config: experiment configuration dict

    Returns:
        all_metrics: MetricsCollector with data from all methods
    """
    print("\n" + "=" * 70)
    print("  FED-MDBSCAN COMPARISON EXPERIMENT")
    print("=" * 70)

    all_metrics = MetricsCollector()
    config = resolve_experiment_config(config)
    methods = config['methods']

    for method in methods:
        method_metrics = run_single_experiment(config, method, seed=config['seed'])

        # Merge records
        all_metrics.records.extend(method_metrics.records)

    return all_metrics


def get_default_config():
    """Return default experiment configuration."""
    return resolve_experiment_config()


def main():
    """Main entry point for running experiments."""
    parser = argparse.ArgumentParser(description='Fed-MDBSCAN Simulation')
    parser.add_argument('--dataset', type=str, default='mnist',
                        choices=['mnist', 'fashion_mnist', 'har', 'cifar10'],
                        help='Dataset to use')
    parser.add_argument('--num_clients', type=int, default=20,
                        help='Number of IoT clients')
    parser.add_argument('--num_rounds', type=int, default=20,
                        help='Number of communication rounds')
    parser.add_argument('--local_epochs', type=int, default=3,
                        help='Local training epochs')
    parser.add_argument('--malicious_ratio', type=float, default=0.0,
                        help='Ratio of malicious clients (0.0 to 1.0)')
    parser.add_argument('--non_iid_alpha', type=float, default=0.5,
                        help='Dirichlet alpha for Non-IID distribution')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument(
        '--output_dir', type=str,
        default='./results/validated/audit-v2/single',
                        help='Output directory for results')
    parser.add_argument('--quick_test', action='store_true',
                        help='Run a quick test with minimal settings')

    args = parser.parse_args()

    # Build config
    overrides = {
        'dataset': args.dataset,
        'num_clients': args.num_clients,
        'num_rounds': args.num_rounds,
        'local_epochs': args.local_epochs,
        'malicious_ratio': args.malicious_ratio,
        'non_iid_alpha': args.non_iid_alpha,
        'seed': args.seed,
        'output_dir': args.output_dir,
    }

    # Quick test mode: minimal settings for validation
    if args.quick_test:
        overrides.update({
            'num_clients': 10,
            'num_rounds': 3,
            'local_epochs': 1,
            'dataset': 'mnist',
        })
        print("\n⚡ QUICK TEST MODE — Minimal settings for validation")

    overrides['output_dir'] = _validated_output_path(overrides['output_dir'])
    config = resolve_experiment_config(overrides)

    # Save config
    os.makedirs(config['output_dir'], exist_ok=True)
    config_path = os.path.join(config['output_dir'], 'experiment_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Config saved: {config_path}")

    # Run comparison
    all_metrics = run_comparison_experiment(config)

    # Save results
    all_metrics.save_csv(os.path.join(config['output_dir'], 'all_results.csv'))
    all_metrics.save_all_methods_csv(config['output_dir'])

    # Generate visualizations
    generate_all_plots(all_metrics, output_dir=config['output_dir'])

    # Print final comparison table
    print("\n" + "=" * 70)
    print("  FINAL COMPARISON SUMMARY")
    print("=" * 70)
    print(f"  {'Method':<25} {'Accuracy':>10} {'FPR':>10} {'TPR':>10} {'Time(s)':>10}")
    print("  " + "-" * 65)

    for method in config['methods']:
        s = all_metrics.get_summary(method)
        if s:
            label = method.replace('_', '-').upper()
            print(f"  {label:<25} "
                  f"{s.get('accuracy_mean', 0):>10.4f} "
                  f"{s.get('fpr_mean', 0):>10.4f} "
                  f"{s.get('tpr_mean', 0):>10.4f} "
                  f"{s.get('time_elapsed_mean', 0):>10.4f}")

    print("\n✅ Experiment complete! Results saved to:", config['output_dir'])


if __name__ == '__main__':
    main()
