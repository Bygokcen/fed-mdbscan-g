"""
Batch experiment runner with resume / atomic-checkpoint guarantees.

Architecture (Faz 1.6):
    For every (scenario, method, seed) triple, exactly one JSON file is
    produced under  scenario_<id>/runs/<method>_seed<S>.json.  Each file is
    written atomically (tmp + os.replace) so a crash never leaves a half
    file. On resume, existing files are detected and skipped.

    scenario_summary.json  ←  aggregate over runs/*.json
    all_results.csv        ←  pandas-concat over runs/*.json
    master_summary.json    ←  aggregate over scenario_summary.json files

Both reductions are pure functions of the on-disk state, so they can be
re-run any time without re-training. CSVs are never appended; they are
re-derived. This eliminates the duplicate / half-row risk of append patterns.

Usage:
    python -m simulation.run_batch_experiments
    python -m simulation.run_batch_experiments --scenarios 1.2,2.3
    python -m simulation.run_batch_experiments --dataset fashion_mnist
"""

import os
import sys
import json
import time
import tempfile
import traceback
import hashlib
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from simulation.run_experiment import run_single_experiment
from simulation.contracts import (
    DEFAULT_EXPERIMENT_CONFIG,
    SCHEMA_VERSION,
    PROTOCOL_VERSION,
    VALIDATED_RUN_NAMESPACE,
    canonical_json,
    resolve_experiment_config,
)


# ============================================================
#  EXPERIMENT SCENARIOS
# ============================================================
SCENARIOS = [
    # Grup 1: Temel Heterojenlik (alpha=0.5)
    {"id": "1.1", "alpha": 0.5, "malicious_ratio": 0.0, "attack_type": "gaussian",          "label": "α=0.5 Clean"},
    {"id": "1.2", "alpha": 0.5, "malicious_ratio": 0.2, "attack_type": "gaussian",          "label": "α=0.5 20% Gaussian"},
    {"id": "1.3", "alpha": 0.5, "malicious_ratio": 0.2, "attack_type": "label_flip",        "label": "α=0.5 20% LabelFlip"},

    # Grup 2: Şiddetli Heterojenlik (alpha=0.1)
    {"id": "2.1", "alpha": 0.1, "malicious_ratio": 0.2, "attack_type": "gaussian",          "label": "α=0.1 20% Gaussian"},
    {"id": "2.2", "alpha": 0.1, "malicious_ratio": 0.2, "attack_type": "label_flip",        "label": "α=0.1 20% LabelFlip"},
    {"id": "2.3", "alpha": 0.1, "malicious_ratio": 0.3, "attack_type": "gaussian",          "label": "α=0.1 30% Gaussian"},

    # Grup 3: Uç Stres Testi (alpha=0.01)
    {"id": "3.1", "alpha": 0.01, "malicious_ratio": 0.2, "attack_type": "gaussian",         "label": "α=0.01 20% Gaussian"},
    {"id": "3.2", "alpha": 0.01, "malicious_ratio": 0.3, "attack_type": "gaussian",         "label": "α=0.01 30% Gaussian"},
    {"id": "3.3", "alpha": 0.01, "malicious_ratio": 0.3, "attack_type": "label_flip",       "label": "α=0.01 30% LabelFlip"},

    # Grup 4: Stealth Gaussian (norm-tabanlı filtreyi kör eden subtle attack)
    {"id": "4.1", "alpha": 0.1,  "malicious_ratio": 0.2, "attack_type": "stealth_gaussian", "label": "α=0.1 20% StealthG"},
    {"id": "4.2", "alpha": 0.01, "malicious_ratio": 0.2, "attack_type": "stealth_gaussian", "label": "α=0.01 20% StealthG"},
    {"id": "4.3", "alpha": 0.01, "malicious_ratio": 0.3, "attack_type": "stealth_gaussian", "label": "α=0.01 30% StealthG"},

    # Grup 5: Adaptive Gaussian (gray-box adaptif saldırgan; norm korunur, yön bozulur)
    {"id": "5.1", "alpha": 0.1,  "malicious_ratio": 0.2, "attack_type": "adaptive_gaussian","label": "α=0.1 20% AdaptiveG"},
    {"id": "5.2", "alpha": 0.01, "malicious_ratio": 0.2, "attack_type": "adaptive_gaussian","label": "α=0.01 20% AdaptiveG"},
    {"id": "5.3", "alpha": 0.01, "malicious_ratio": 0.3, "attack_type": "adaptive_gaussian","label": "α=0.01 30% AdaptiveG"},

    # Clean controls at the same severe heterogeneity levels.
    {"id": "6.1", "alpha": 0.1, "malicious_ratio": 0.0, "attack_type": "gaussian", "label": "α=0.1 Clean"},
    {"id": "6.2", "alpha": 0.01,"malicious_ratio": 0.0, "attack_type": "gaussian", "label": "α=0.01 Clean"},
]

METHODS = ['fed_mdbscan_g', 'fed_dbscan', 'fed_rra', 'fed_g2l',
           'fedavg', 'krum', 'coord_median', 'fltrust', 'flame']


class BatchContractError(RuntimeError):
    """Raised when cached or newly-created evidence violates the protocol."""


class IncompleteBatchError(BatchContractError):
    """Raised when canonical reductions are requested before every unit is valid."""


METHOD_VERSION = 'audit-method-contract-v2'
ATTACK_VERSION = 'audit-attack-contract-v2'
REQUIRED_RUN_METADATA = {
    'dataset_identity', 'partition_sha256', 'initial_model_sha256',
    'model_identity', 'command', 'start_time_unix', 'end_time_unix',
    'peak_memory_kib', 'runtime', 'resolved_config',
}


# ============================================================
#  Atomic / resume helpers
# ============================================================

def _atomic_write_json(path, data):
    """Write JSON atomically: stage to a temp file in the same directory,
    fsync, then os.replace into place. A crash leaves either the old file
    intact or the fully-written new file — never a partial write."""
    d = os.path.dirname(path) or '.'
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.tmp_', suffix='.json')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


def _run_unit_path(scenario_dir, method, seed):
    """Where the per-(method, seed) result lives."""
    return os.path.join(scenario_dir, 'runs', f'{method}_seed{seed}.json')


def _failure_unit_path(scenario_dir, method, seed):
    return os.path.join(scenario_dir, 'failures', f'{method}_seed{seed}.json')


def _remove_if_exists(path):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _invalidate_scenario_outputs(scenario_dir):
    for name in ('scenario_summary.json', 'all_results.csv'):
        _remove_if_exists(os.path.join(scenario_dir, name))


def _invalidate_master_output(base_output_dir):
    _remove_if_exists(os.path.join(base_output_dir, 'master_summary.json'))


def _normalise_matrix(methods, seeds):
    if isinstance(methods, (str, bytes)) or isinstance(seeds, (str, bytes)):
        raise BatchContractError('methods and seeds must be iterable dimensions, not strings')
    method_values = tuple(methods)
    seed_values = tuple(seeds)
    if (not method_values or any(not isinstance(item, str) or not item for item in method_values)
            or len(set(method_values)) != len(method_values)):
        raise BatchContractError('methods must be non-empty unique strings')
    if (not seed_values
            or any(isinstance(item, bool) or not isinstance(item, (int, np.integer))
                   or item < 0 or item > 2**32 - 1 for item in seed_values)
            or len(set(int(item) for item in seed_values)) != len(seed_values)):
        raise BatchContractError('seeds must be non-empty unique uint32 integers')
    return method_values, tuple(int(item) for item in seed_values)


def _ensure_validated_output_dir(output_dir):
    project_root = Path(__file__).resolve().parents[2]
    target = Path(output_dir).resolve()
    legacy_roots = (
        project_root / 'new_work/results/heterogeneous_v3_mnist',
        project_root / 'new_work/results/heterogeneous_v3_fashion_mnist',
        project_root / 'new_work/results/heterogeneous_v3_har',
        project_root / 'new_work/results/phase2b_report',
    )
    for legacy in legacy_roots:
        try:
            target.relative_to(legacy.resolve())
        except ValueError:
            continue
        raise BatchContractError('validated output cannot be inside a legacy result root')
    results_root = (project_root / 'new_work/results').resolve()
    validated_root = (results_root / VALIDATED_RUN_NAMESPACE).resolve()
    try:
        target.relative_to(results_root)
    except ValueError:
        pass
    else:
        try:
            target.relative_to(validated_root)
        except ValueError as exc:
            raise BatchContractError(
                f'new_work/results outputs must use results/{VALIDATED_RUN_NAMESPACE}',
            ) from exc
    return str(target)


def _sha256_json(value):
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _unit_identity(protocol_digest, scenario_id, method, seed):
    return _sha256_json({
        'protocol_digest': protocol_digest,
        'scenario_id': str(scenario_id),
        'method': method,
        'seed': int(seed),
    })


def _dependency_lock_digest(project_root=None):
    root = project_root or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    entries = []
    for name in ('requirements.txt', 'requirements-dev.txt'):
        path = os.path.join(root, name)
        if os.path.isfile(path):
            with open(path, 'rb') as handle:
                entries.append({'path': name, 'sha256': hashlib.sha256(handle.read()).hexdigest()})
    return _sha256_json(entries)


def _source_state():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    try:
        commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], cwd=root, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        status = subprocess.run(
            ['git', 'status', '--porcelain', '--untracked-files=all', '--',
             'new_work/simulation', 'requirements.txt', 'requirements-dev.txt'], cwd=root,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        dirty = bool(status)
    except (OSError, subprocess.SubprocessError):
        commit, dirty, status = 'unavailable', None, 'unavailable'
    provenance = Path(root) / 'source_provenance.json'
    if provenance.exists():
        frozen = json.loads(provenance.read_text())
        commit, dirty = frozen['commit'], frozen['dirty']
        frozen_status_digest = frozen['dirty_state_sha256']
    else:
        frozen_status_digest = hashlib.sha256(status.encode('utf-8')).hexdigest()
    sources = {}
    simulation_dir = Path(__file__).resolve().parent
    for path in sorted(simulation_dir.glob('*.py')):
        with path.open('rb') as handle:
            sources[path.name] = hashlib.sha256(handle.read()).hexdigest()
    return {
        'commit': commit,
        'dirty': dirty,
        'dirty_state_sha256': frozen_status_digest,
        'source_files': sources,
        'source_digest': _sha256_json(sources),
    }


def _environment_state():
    import scipy
    import sklearn
    return {
        'python': platform.python_version(),
        'platform': platform.platform(),
        'numpy': np.__version__,
        'pandas': pd.__version__,
        'scipy': scipy.__version__,
        'scikit_learn': sklearn.__version__,
        'torch': torch.__version__,
        'dependency_lock_digest': _dependency_lock_digest(),
        'deterministic_backend': bool(torch.are_deterministic_algorithms_enabled()),
        'cuda_available': bool(torch.cuda.is_available()),
    }


def _validate_records(records, expected_rounds, expected_method):
    if not isinstance(records, list) or len(records) != expected_rounds:
        raise BatchContractError(
            f'unit records must contain exactly {expected_rounds} rounds'
        )
    required = (
        'round', 'method', 'accuracy', 'fpr', 'tpr', 'time_elapsed',
        'participant_ids', 'update_ids', 'accepted_ids', 'rejected_ids',
        'fallback_applied', 'fallback_reason', 'degraded',
    )
    for expected_round, record in enumerate(records):
        if not isinstance(record, dict) or any(key not in record for key in required):
            raise BatchContractError('unit record is malformed')
        if (isinstance(record['round'], bool)
                or not isinstance(record['round'], (int, np.integer))
                or record['round'] != expected_round):
            raise BatchContractError('unit round sequence is not contiguous')
        if record['method'] != expected_method:
            raise BatchContractError('unit record method does not match its unit')
        for key in ('accuracy', 'fpr', 'tpr', 'time_elapsed'):
            value = record[key]
            if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
                raise BatchContractError(f'unit record {key} is not numeric')
            if not np.isfinite(value):
                raise BatchContractError(f'unit record {key} is non-finite')
        for key in ('accuracy', 'fpr', 'tpr'):
            if not 0.0 <= float(record[key]) <= 1.0:
                raise BatchContractError(f'unit record {key} is outside [0, 1]')
        if float(record['time_elapsed']) < 0.0:
            raise BatchContractError('unit record time_elapsed must be non-negative')
        id_fields = ('participant_ids', 'update_ids', 'accepted_ids', 'rejected_ids')
        if any(not isinstance(record[key], list) for key in id_fields):
            raise BatchContractError('unit record identity fields must be lists')
        participants = record['participant_ids']
        updates = record['update_ids']
        accepted = record['accepted_ids']
        rejected = record['rejected_ids']
        try:
            if (len(set(participants)) != len(participants)
                    or len(set(updates)) != len(updates)
                    or len(set(accepted)) != len(accepted)
                    or len(set(rejected)) != len(rejected)):
                raise BatchContractError('unit record identity fields contain duplicates')
            if set(accepted) & set(rejected) or set(accepted) | set(rejected) != set(participants):
                raise BatchContractError('unit record decision does not partition participants')
        except TypeError as exc:
            raise BatchContractError('unit record identities must be hashable') from exc
        if len(updates) != len(participants):
            raise BatchContractError('unit record update IDs do not map to participants')
        if (not isinstance(record['fallback_applied'], (bool, int, np.integer))
                or int(record['fallback_applied']) not in (0, 1)):
            raise BatchContractError('fallback_applied must be boolean-like')
        if (not isinstance(record['degraded'], (bool, int, np.integer))
                or int(record['degraded']) not in (0, 1)):
            raise BatchContractError('degraded must be boolean-like')
        if not isinstance(record['fallback_reason'], str):
            raise BatchContractError('fallback_reason must be a string')
        from simulation.metrics import evaluate_detection_decision
        for field in ('tp', 'fp', 'tn', 'fn', 'actual_malicious_ids', 'n_participants', 'n_malicious'):
            if field not in record:
                raise BatchContractError(f'audit-v2 record missing {field}')
        truth = record['actual_malicious_ids']
        if not isinstance(truth, list) or len(set(truth)) != len(truth) or not set(truth) <= set(participants):
            raise BatchContractError('invalid actual malicious identities')
        computed = evaluate_detection_decision({'accepted_ids': accepted, 'rejected_ids': rejected}, truth)
        for field in ('tp', 'fp', 'tn', 'fn', 'fpr', 'tpr'):
            if abs(float(record[field]) - computed[field]) > 1e-12:
                raise BatchContractError(f'decision/count mismatch: {field}')
        if record['n_participants'] != len(participants) or record['n_malicious'] != len(truth):
            raise BatchContractError('participant denominator mismatch')
        if participants and len(truth) * 2 >= len(participants):
            raise BatchContractError('honest majority violated')
        stack = list(record.values())
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                stack.extend(value.values())
            elif isinstance(value, (list, tuple)):
                stack.extend(value)
            elif isinstance(value, (float, np.floating)) and not np.isfinite(value):
                raise BatchContractError('unit record contains a non-finite value')


def _validate_run_metadata(run_metadata, resolved_config):
    if not isinstance(run_metadata, dict):
        raise BatchContractError('run_metadata must be a dictionary')
    missing = sorted(REQUIRED_RUN_METADATA - set(run_metadata))
    if missing:
        raise BatchContractError(f'run_metadata is incomplete: {missing}')
    if run_metadata['resolved_config'] != resolved_config:
        raise BatchContractError('run_metadata resolved_config mismatch')
    def _is_sha256(value):
        return (isinstance(value, str) and len(value) == 64
                and all(char in '0123456789abcdef' for char in value))

    for key in ('partition_sha256', 'initial_model_sha256'):
        value = run_metadata[key]
        if not _is_sha256(value):
            raise BatchContractError(f'run_metadata {key} is not a SHA-256 digest')
    dataset = run_metadata['dataset_identity']
    if not isinstance(dataset, dict) or not {'name', 'train', 'test'} <= set(dataset):
        raise BatchContractError('dataset identity is incomplete')
    if dataset['name'] != resolved_config['dataset']:
        raise BatchContractError('dataset identity does not match resolved config')
    for split in ('train', 'test'):
        identity = dataset[split]
        if (not isinstance(identity, dict)
                or not {'class', 'length', 'transform', 'target_transform', 'sha256'} <= set(identity)
                or not _is_sha256(identity.get('sha256'))
                or isinstance(identity.get('length'), bool)
                or not isinstance(identity.get('length'), int)
                or identity['length'] <= 0):
            raise BatchContractError(f'dataset {split} identity is incomplete')
    model = run_metadata['model_identity']
    if (not isinstance(model, dict)
            or not {'class', 'repr', 'parameters', 'sha256'} <= set(model)
            or not isinstance(model.get('parameters'), list)
            or not _is_sha256(model.get('sha256'))):
        raise BatchContractError('model identity is incomplete')
    command = run_metadata['command']
    if not isinstance(command, list) or any(not isinstance(item, str) for item in command):
        raise BatchContractError('run command must be a string list')
    start = run_metadata['start_time_unix']
    end = run_metadata['end_time_unix']
    peak = run_metadata['peak_memory_kib']
    for key, value in (('start_time_unix', start), ('end_time_unix', end),
                       ('peak_memory_kib', peak)):
        if (isinstance(value, bool) or not isinstance(value, (int, float, np.number))
                or not np.isfinite(value) or float(value) < 0.0):
            raise BatchContractError(f'run_metadata {key} must be non-negative and finite')
    if float(end) < float(start):
        raise BatchContractError('run end precedes run start')
    if not isinstance(run_metadata['runtime'], dict):
        raise BatchContractError('runtime metadata must be a dictionary')


def _build_unit(config, scenario, method, seed, records, run_metadata=None):
    resolved = resolve_experiment_config({**config, 'seed': int(seed)})
    _validate_records(records, resolved['num_rounds'], method)
    _validate_run_metadata(run_metadata, resolved)
    payload = {
        'schema_version': SCHEMA_VERSION,
        'protocol_version': PROTOCOL_VERSION,
        'validated_run_namespace': VALIDATED_RUN_NAMESPACE,
        'protocol_digest': resolved['protocol_digest'],
        'unit_identity': _unit_identity(
            resolved['protocol_digest'], scenario['id'], method, seed,
        ),
        'scenario_id': str(scenario['id']),
        'scenario': dict(scenario),
        'method': method,
        'method_version': METHOD_VERSION,
        'attack_version': ATTACK_VERSION,
        'seed': int(seed),
        'resolved_config': resolved,
        'source': _source_state(),
        'environment': _environment_state(),
        'run_metadata': dict(run_metadata),
        'start_time_unix': run_metadata['start_time_unix'],
        'end_time_unix': run_metadata['end_time_unix'],
        'peak_memory_kib': run_metadata['peak_memory_kib'],
        'exit_status': 0,
        'records': records,
    }
    payload['payload_sha256'] = _sha256_json(payload)
    return payload


def _validate_unit(unit, scenario_id, method, seed, resolved_config):
    if not isinstance(unit, dict):
        raise BatchContractError('unit must be a JSON object')
    metadata = unit.get('run_metadata')
    metadata = metadata if isinstance(metadata, dict) else {}
    expected = {
        'schema_version': SCHEMA_VERSION,
        'protocol_version': PROTOCOL_VERSION,
        'validated_run_namespace': VALIDATED_RUN_NAMESPACE,
        'protocol_digest': resolved_config['protocol_digest'],
        'unit_identity': _unit_identity(
            resolved_config['protocol_digest'], scenario_id, method, seed,
        ),
        'scenario_id': str(scenario_id),
        'method': method,
        'method_version': METHOD_VERSION,
        'attack_version': ATTACK_VERSION,
        'seed': int(seed),
        'exit_status': 0,
        'start_time_unix': metadata.get('start_time_unix'),
        'end_time_unix': metadata.get('end_time_unix'),
        'peak_memory_kib': metadata.get('peak_memory_kib'),
    }
    mismatches = [key for key, value in expected.items() if unit.get(key) != value]
    if unit.get('resolved_config') != resolve_experiment_config(
            {**resolved_config, 'seed': int(seed)}):
        mismatches.append('resolved_config')
    scenario = unit.get('scenario')
    if not isinstance(scenario, dict) or str(scenario.get('id')) != str(scenario_id):
        mismatches.append('scenario')
    current_source = _source_state()
    if unit.get('source') != current_source:
        mismatches.append('source')
    current_environment = _environment_state()
    if unit.get('environment') != current_environment:
        mismatches.append('environment')
    stored_checksum = unit.get('payload_sha256')
    unsigned = dict(unit)
    unsigned.pop('payload_sha256', None)
    if stored_checksum != _sha256_json(unsigned):
        mismatches.append('payload_sha256')
    if mismatches:
        raise BatchContractError(
            f'incompatible cached unit {method}/seed={seed}: {sorted(set(mismatches))}'
        )
    _validate_run_metadata(unit.get('run_metadata'), resolve_experiment_config(
        {**resolved_config, 'seed': int(seed)}
    ))
    _validate_records(unit.get('records'), resolved_config['num_rounds'], method)
    return unit


def _read_valid_unit(path, scenario_id, method, seed, resolved_config):
    try:
        with open(path, encoding='utf-8') as handle:
            unit = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise BatchContractError(f'cached unit is unreadable: {path}: {exc}') from exc
    return _validate_unit(unit, scenario_id, method, seed, resolved_config)


def _aggregate_method_records(method, records):
    """Compute uncertainty across independent unit endpoints, never pooled rounds."""
    if not records:
        return None
    df = pd.DataFrame(records)
    summary = {
        'accuracy_mean': float(df['accuracy'].mean()),
        'accuracy_std':  float(df['accuracy'].std()) if len(df) > 1 else 0.0,
        'fpr_mean':      float(df['fpr'].mean()),
        'fpr_std':       float(df['fpr'].std()) if len(df) > 1 else 0.0,
        'tpr_mean':      float(df['tpr'].mean()),
        'tpr_std':       float(df['tpr'].std()) if len(df) > 1 else 0.0,
        'time_mean':     float(df['time_elapsed'].mean()),
        'n_units':       int(len(df)),
    }
    if method == 'fed_mdbscan_g' and 'alert_tp' in df.columns:
        atp = int(df['alert_tp'].sum())
        afp = int(df['alert_fp'].sum())
        afn = int(df['alert_fn'].sum())
        atn = int(df['alert_tn'].sum())
        total = atp + afp + afn + atn
        summary.update({
            'alert_tp': atp, 'alert_fp': afp,
            'alert_fn': afn, 'alert_tn': atn,
            'alert_accuracy':  (atp + atn) / max(total, 1),
            'alert_recall':    atp / max(atp + afn, 1),
            'alert_precision': atp / max(atp + afp, 1),
            'gap_concentration_mean': float(
                df.get('gap_concentration', pd.Series([0])).mean()
            ),
        })
        diagnostic_cols = {
            'density_gap_detected': 'density_gap_rate',
            'attack_gate': 'attack_gate_rate',
            'attack_alert': 'attack_alert_rate',
            'l0_rejected_count': 'l0_rejected_mean',
            'l2_rejected_count': 'l2_rejected_mean',
            'low_density_count': 'low_density_mean',
            'natural_clusters_count': 'natural_clusters_mean',
            'rejected_snnc_clusters': 'rejected_snnc_clusters_mean',
        }
        for col, out_key in diagnostic_cols.items():
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce').fillna(0)
                summary[out_key] = float(values.mean())
    return summary


def _unit_endpoint(unit):
    records = unit['records']
    final = records[-1]
    endpoint = {
        'accuracy': float(final['accuracy']),
        'fpr': float(np.mean([record['fpr'] for record in records])),
        'tpr': float(np.mean([record['tpr'] for record in records])),
        'time_elapsed': float(np.sum([record['time_elapsed'] for record in records])),
    }
    for key in ('alert_tp', 'alert_fp', 'alert_fn', 'alert_tn'):
        if all(key in record for record in records):
            endpoint[key] = int(sum(record[key] for record in records))
    for key in (
        'gap_concentration', 'density_gap_detected', 'attack_gate', 'attack_alert',
        'l0_rejected_count', 'l2_rejected_count', 'low_density_count',
        'natural_clusters_count', 'rejected_snnc_clusters',
    ):
        if all(key in record for record in records):
            endpoint[key] = float(np.mean([record[key] for record in records]))
    return endpoint


def _atomic_write_csv(path, records):
    directory = os.path.dirname(path) or '.'
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=directory, prefix='.tmp_', suffix='.csv',
    )
    os.close(descriptor)
    try:
        pd.DataFrame(records).to_csv(temporary, index=False)
        with open(temporary, 'rb') as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        _remove_if_exists(temporary)
        raise


def _reduce_scenario(scenario_dir, scenario_meta, methods, seeds, resolved_config):
    """Write canonical outputs only when every expected unit is valid."""
    _invalidate_scenario_outputs(scenario_dir)
    methods, seeds = _normalise_matrix(methods, seeds)
    summary = dict(scenario_meta)
    summary['schema_version'] = SCHEMA_VERSION
    summary['methods'] = {}
    summary['seeds'] = list(seeds)
    summary['expected_methods'] = list(methods)
    summary['protocol_digest'] = resolved_config['protocol_digest']
    summary['unit_references'] = []
    all_records = []
    missing = []
    for method in methods:
        method_records = []
        seeds_done = []
        for seed in seeds:
            path = _run_unit_path(scenario_dir, method, seed)
            if not os.path.exists(path):
                failure_path = _failure_unit_path(scenario_dir, method, seed)
                reason = 'missing'
                if os.path.exists(failure_path):
                    try:
                        with open(failure_path, encoding='utf-8') as handle:
                            failure = json.load(handle)
                        unsigned_failure = dict(failure)
                        checksum = unsigned_failure.pop('payload_sha256', None)
                        if (checksum != _sha256_json(unsigned_failure)
                                or failure.get('unit_identity') != _unit_identity(
                                    resolved_config['protocol_digest'],
                                    scenario_meta['scenario_id'], method, seed,
                                )
                                or failure.get('exit_status') == 0):
                            reason = 'invalid failure artifact'
                        else:
                            reason = failure.get('reason', 'failed unit')
                    except (OSError, json.JSONDecodeError):
                        reason = 'unreadable failure artifact'
                missing.append({'method': method, 'seed': seed, 'reason': reason})
                continue
            try:
                unit = _read_valid_unit(
                    path, scenario_meta['scenario_id'], method, seed, resolved_config,
                )
            except BatchContractError as exc:
                missing.append({'method': method, 'seed': seed, 'reason': str(exc)})
                continue
            recs = unit['records']
            method_records.append(_unit_endpoint(unit))
            summary['unit_references'].append({
                'unit_identity': unit['unit_identity'],
                'payload_sha256': unit['payload_sha256'],
                'method': method,
                'seed': seed,
            })
            for record in recs:
                all_records.append({
                    **record,
                    'scenario_id': scenario_meta['scenario_id'],
                    'seed': seed,
                    'unit_identity': unit['unit_identity'],
                    'unit_payload_sha256': unit['payload_sha256'],
                })
            seeds_done.append(seed)
        ms = _aggregate_method_records(method, method_records)
        if ms is not None:
            ms['n_seeds'] = len(seeds_done)
            ms['seeds_done'] = seeds_done
            summary['methods'][method] = ms

    progress = {
        'schema_version': SCHEMA_VERSION,
        'protocol_digest': resolved_config['protocol_digest'],
        'scenario_id': scenario_meta['scenario_id'],
        'complete': not missing,
        'valid_units': len(methods) * len(seeds) - len(missing),
        'expected_units': len(methods) * len(seeds),
        'issues': missing,
    }
    _atomic_write_json(os.path.join(scenario_dir, 'scenario_progress.json'), progress)
    if missing:
        raise IncompleteBatchError(
            f"scenario {scenario_meta['scenario_id']} incomplete: "
            f"{len(missing)} invalid or missing unit(s)"
        )

    summary['complete'] = True
    summary['unit_references'] = sorted(
        summary['unit_references'], key=lambda item: (item['method'], item['seed'])
    )
    csv_path = os.path.join(scenario_dir, 'all_results.csv')
    _atomic_write_csv(csv_path, all_records)
    summary['all_results_rows'] = len(all_records)
    summary['all_results_sha256'] = _sha256_file(csv_path)
    _atomic_write_json(
        os.path.join(scenario_dir, 'scenario_summary.json'), summary
    )
    return summary


def _reduce_master(base_output_dir, selected):
    """Write a canonical master only if every selected scenario is complete."""
    _invalidate_master_output(base_output_dir)
    if not selected:
        raise BatchContractError('at least one scenario must be selected')
    if any(not isinstance(item, dict) or 'id' not in item for item in selected):
        raise BatchContractError('selected scenarios must be dictionaries with identities')
    if len({str(item.get('id')) for item in selected if isinstance(item, dict)}) != len(selected):
        raise BatchContractError('selected scenarios must have unique identities')
    summaries = []
    missing = []
    for sc in selected:
        path = os.path.join(
            base_output_dir, f"scenario_{sc['id']}", 'scenario_summary.json'
        )
        if os.path.exists(path):
            try:
                with open(path) as f:
                    summary = json.load(f)
                contract_path = os.path.join(
                    base_output_dir, f"scenario_{sc['id']}", 'scenario_config.json',
                )
                with open(contract_path, encoding='utf-8') as handle:
                    contract = json.load(handle)
                unsigned_contract = dict(contract)
                fingerprint = unsigned_contract.pop('scenario_fingerprint', None)
                expected_methods, expected_seeds = _normalise_matrix(
                    contract.get('methods', []), contract.get('seeds', []),
                )
                config_payload = dict(contract)
                for key in ('scenario', 'seeds', 'scenario_fingerprint'):
                    config_payload.pop(key, None)
                resolved_contract = resolve_experiment_config(config_payload)
                required = {
                    'schema_version': SCHEMA_VERSION,
                    'scenario_id': str(sc['id']),
                    'label': contract.get('scenario', {}).get('label'),
                    'dataset': contract.get('dataset'),
                    'alpha': contract.get('scenario', {}).get('alpha'),
                    'malicious_ratio': contract.get('scenario', {}).get('malicious_ratio'),
                    'attack_type': contract.get('scenario', {}).get('attack_type'),
                    'num_clients': contract.get('num_clients'),
                    'num_rounds': contract.get('num_rounds'),
                    'dropout_rate': contract.get('dropout_rate'),
                    'data_size_sigma': contract.get('data_size_sigma'),
                    'protocol_digest': contract.get('protocol_digest'),
                    'complete': True,
                    'expected_methods': list(expected_methods),
                    'seeds': list(expected_seeds),
                }
                mismatches = [
                    key for key, value in required.items() if summary.get(key) != value
                ]
                if fingerprint != _sha256_json(unsigned_contract):
                    mismatches.append('scenario_fingerprint')
                references = summary.get('unit_references')
                expected_units = len(expected_methods) * len(expected_seeds)
                if not isinstance(references, list) or len(references) != expected_units:
                    mismatches.append('unit_references')
                elif len({item.get('unit_identity') for item in references
                          if isinstance(item, dict)}) != expected_units:
                    mismatches.append('unit_reference_identity')
                else:
                    reference_map = {
                        (item.get('method'), item.get('seed')): item
                        for item in references if isinstance(item, dict)
                    }
                    recomputed_methods = {}
                    for method in expected_methods:
                        endpoints = []
                        for seed in expected_seeds:
                            unit = _read_valid_unit(
                                _run_unit_path(os.path.dirname(path), method, seed),
                                sc['id'], method, seed, resolved_contract,
                            )
                            reference = reference_map.get((method, seed), {})
                            if (reference.get('unit_identity') != unit['unit_identity']
                                    or reference.get('payload_sha256') != unit['payload_sha256']):
                                mismatches.append('unit_reference_hash')
                            endpoints.append(_unit_endpoint(unit))
                        method_summary = _aggregate_method_records(method, endpoints)
                        method_summary['n_seeds'] = len(expected_seeds)
                        method_summary['seeds_done'] = list(expected_seeds)
                        recomputed_methods[method] = method_summary
                    if summary.get('methods') != recomputed_methods:
                        mismatches.append('method_summaries')
                if set(summary.get('methods', {})) != set(expected_methods):
                    mismatches.append('methods')
                csv_path = os.path.join(os.path.dirname(path), 'all_results.csv')
                try:
                    if summary.get('all_results_sha256') != _sha256_file(csv_path):
                        mismatches.append('all_results_sha256')
                    if summary.get('all_results_rows') != sum(
                            len(_read_valid_unit(
                                _run_unit_path(os.path.dirname(path), method, seed),
                                sc['id'], method, seed, resolved_contract,
                            )['records'])
                            for method in expected_methods for seed in expected_seeds):
                        mismatches.append('all_results_rows')
                except OSError:
                    mismatches.append('all_results_csv')
                if mismatches:
                    raise BatchContractError(
                        f'invalid scenario summary {path}: {sorted(set(mismatches))}'
                    )
                summaries.append(summary)
            except (
                json.JSONDecodeError, OSError, BatchContractError,
                TypeError, ValueError, KeyError,
            ) as e:
                missing.append(f'{path}: {e}')
        else:
            missing.append(path)
    _atomic_write_json(os.path.join(base_output_dir, 'master_progress.json'), {
        'complete': not missing,
        'valid_scenarios': len(summaries),
        'expected_scenarios': len(selected),
        'issues': missing,
    })
    if missing:
        raise IncompleteBatchError(
            f'master incomplete: {len(missing)} scenario summary file(s) missing or invalid'
        )
    _atomic_write_json(
        os.path.join(base_output_dir, 'master_summary.json'), {
            'schema_version': SCHEMA_VERSION,
            'complete': True,
            'scenario_ids': [str(sc['id']) for sc in selected],
            'scenario_summaries': summaries,
        }
    )
    return summaries


# ============================================================
#  Scenario runner with resume
# ============================================================

def run_scenario(
                 scenario,
                 base_output_dir=f'./results/{VALIDATED_RUN_NAMESPACE}/heterogeneous',
                 num_clients=100, num_rounds=30,
                 seeds=(42, 137, 2024),
                 dropout_rate=0.10, data_size_sigma=0.5,
                 dataset='mnist', methods=None, config_overrides=None):
    """Run all (method, seed) units for a scenario. Existing on-disk units
    are skipped (resume). After every unit (and at the end) the scenario
    summary + all_results.csv are re-derived from runs/*.json.
    """
    if not isinstance(scenario, dict) or not {'id', 'label', 'alpha', 'malicious_ratio', 'attack_type'} <= set(scenario):
        raise BatchContractError('scenario is incomplete')
    reserved = {'dataset', 'num_clients', 'num_rounds', 'non_iid_alpha', 'malicious_ratio',
                'attack_type', 'dropout_rate', 'data_size_sigma', 'output_dir', 'methods', 'seed'}
    if reserved & set(config_overrides or {}):
        raise BatchContractError('scenario identity must be set through scenario/runner arguments')
    base_output_dir = _ensure_validated_output_dir(base_output_dir)
    scenario_id = str(scenario['id'])
    scenario_dir = os.path.join(base_output_dir, f"scenario_{scenario_id}")
    os.makedirs(os.path.join(scenario_dir, 'runs'), exist_ok=True)
    _invalidate_scenario_outputs(scenario_dir)
    methods, seeds = _normalise_matrix(
        METHODS if methods is None else methods, seeds)
    _atomic_write_json(os.path.join(scenario_dir, 'scenario_progress.json'), {
        'schema_version': SCHEMA_VERSION,
        'scenario_id': scenario_id,
        'complete': False,
        'status': 'validating_contract_and_cache',
        'valid_units': 0,
        'expected_units': len(methods) * len(seeds),
        'issues': [],
    })

    config = resolve_experiment_config({
        'dataset': scenario.get('dataset', dataset),
        'num_clients': num_clients,
        'num_rounds': num_rounds,
        'local_epochs': 3,
        'lr': 0.01,
        'non_iid_alpha': scenario['alpha'],
        'malicious_ratio': scenario['malicious_ratio'],
        'attack_type': scenario['attack_type'],
        'iid': False,
        'dropout_rate': dropout_rate,
        'data_size_sigma': data_size_sigma,
        **(config_overrides or {}),
        'output_dir': scenario_dir,
        'methods': list(methods),
    })

    scenario_meta = {
        'scenario_id': scenario_id,
        'label': scenario['label'],
        'dataset': config['dataset'],
        'alpha': scenario['alpha'],
        'malicious_ratio': scenario['malicious_ratio'],
        'attack_type': scenario['attack_type'],
        'num_clients': num_clients,
        'num_rounds': num_rounds,
        'dropout_rate': dropout_rate,
        'data_size_sigma': data_size_sigma,
    }

    scenario_contract = {**config, 'scenario': dict(scenario), 'seeds': list(seeds)}
    scenario_contract['scenario_fingerprint'] = _sha256_json(scenario_contract)
    config_path = os.path.join(scenario_dir, 'scenario_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding='utf-8') as handle:
                cached_contract = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            _atomic_write_json(os.path.join(scenario_dir, 'scenario_progress.json'), {
                'schema_version': SCHEMA_VERSION,
                'scenario_id': scenario_id,
                'complete': False,
                'status': 'invalid_scenario_contract',
                'valid_units': 0,
                'expected_units': len(methods) * len(seeds),
                'issues': [str(exc)],
            })
            raise BatchContractError(f'invalid cached scenario contract: {exc}') from exc
        if cached_contract != scenario_contract:
            _atomic_write_json(os.path.join(scenario_dir, 'scenario_progress.json'), {
                'schema_version': SCHEMA_VERSION,
                'scenario_id': scenario_id,
                'complete': False,
                'status': 'incompatible_scenario_contract',
                'valid_units': 0,
                'expected_units': len(methods) * len(seeds),
                'issues': ['cached scenario contract fingerprint mismatch'],
            })
            raise BatchContractError('cached scenario contract fingerprint mismatch')
    else:
        _atomic_write_json(config_path, scenario_contract)

    print(f"\n{'#'*70}")
    print(f"  SCENARIO {scenario_id}: {scenario['label']}")
    print(f"  Dataset={config['dataset']} | N={num_clients} | Rounds={num_rounds} | Seeds={list(seeds)}")
    print(f"  Alpha={scenario['alpha']} | Malicious={scenario['malicious_ratio']*100:.0f}% | Attack={scenario['attack_type']}")
    print(f"  Dropout={dropout_rate*100:.0f}% (fixed cohort; attackers always participate) | DataSizeSigma={data_size_sigma}")
    print(f"{'#'*70}")

    # Pre-scan: which units already exist?
    todo = []
    cached = 0
    for method in methods:
        for seed in seeds:
            unit_path = _run_unit_path(scenario_dir, method, seed)
            if os.path.exists(unit_path):
                try:
                    _read_valid_unit(unit_path, scenario_id, method, seed, config)
                except BatchContractError as exc:
                    _atomic_write_json(
                        os.path.join(scenario_dir, 'scenario_progress.json'), {
                            'schema_version': SCHEMA_VERSION,
                            'protocol_digest': config['protocol_digest'],
                            'scenario_id': scenario_id,
                            'complete': False,
                            'status': 'incompatible_cached_unit',
                            'valid_units': cached,
                            'expected_units': len(methods) * len(seeds),
                            'issues': [{
                                'method': method, 'seed': seed, 'reason': str(exc),
                            }],
                        },
                    )
                    raise
                cached += 1
            else:
                todo.append((method, seed))
    total = len(methods) * len(seeds)
    print(f"  [resume] {cached}/{total} units already cached, {len(todo)} to run")

    # Execute missing units
    for method, seed in todo:
        unit_path = _run_unit_path(scenario_dir, method, seed)
        failure_path = _failure_unit_path(scenario_dir, method, seed)
        print(f"  [run]    {method}  seed={seed}")
        unit_started = time.time()
        try:
            method_metrics = run_single_experiment(config, method, seed=seed)
            unit = _build_unit(
                config, scenario, method, seed, method_metrics.records,
                getattr(method_metrics, 'run_metadata', None),
            )
            _atomic_write_json(unit_path, unit)
            _remove_if_exists(failure_path)
        except Exception as e:
            print(f"  [error]  {method} seed={seed}: {e}")
            traceback.print_exc()
            failure = {
                'schema_version': SCHEMA_VERSION,
                'protocol_version': PROTOCOL_VERSION,
                'validated_run_namespace': VALIDATED_RUN_NAMESPACE,
                'protocol_digest': config['protocol_digest'],
                'unit_identity': _unit_identity(
                    config['protocol_digest'], scenario_id, method, seed,
                ),
                'scenario_id': scenario_id,
                'method': method,
                'seed': seed,
                'start_time_unix': unit_started,
                'end_time_unix': time.time(),
                'exit_status': 1,
                'reason_code': type(e).__name__,
                'reason': str(e),
            }
            failure['payload_sha256'] = _sha256_json(failure)
            _atomic_write_json(failure_path, failure)
            # Do not write the canonical unit file; the next run retries it.

    # Final reduce (covers the all-cached fast-path too)
    summary = _reduce_scenario(scenario_dir, scenario_meta, methods, seeds, config)

    # Print scenario table from the reduced summary
    print(f"\n  {'Method':<20} {'Accuracy':>10} {'FPR':>10} {'TPR':>10} {'Time(s)':>10}")
    print(f"  {'-'*60}")
    for method in methods:
        m = summary['methods'].get(method, {})
        if m:
            print(f"  {method:<20} "
                  f"{m.get('accuracy_mean', 0):>10.4f} "
                  f"{m.get('fpr_mean', 0):>10.4f} "
                  f"{m.get('tpr_mean', 0):>10.4f} "
                  f"{m.get('time_mean', 0):>10.4f}")
    return summary


def _main():
    """Run all selected scenarios; resume-safe end-to-end."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--output_dir', default=f'./results/{VALIDATED_RUN_NAMESPACE}/heterogeneous',
                    help='Where batch results are written. Re-running with '
                         'the same path resumes from any completed units.')
    ap.add_argument('--num_clients', type=int, default=100,
                    help='Number of IoT clients per scenario.')
    ap.add_argument('--num_rounds', type=int, default=30,
                    help='Number of communication rounds.')
    ap.add_argument('--seeds', default='42,137,2024',
                    help='Comma-separated seed list (averaging).')
    ap.add_argument('--dropout_rate', type=float, default=0.10,
                    help='Fixed fraction absent from each round (audit-v2).')
    ap.add_argument('--data_size_sigma', type=float, default=0.5,
                    help='Lognormal sigma for per-client data size variance '
                         '(0 = uniform).')
    ap.add_argument('--dataset', default='mnist',
                    choices=['mnist', 'fashion_mnist', 'har', 'cifar10'],
                    help='Dataset to use across all scenarios (override per '
                         'scenario by setting scenario["dataset"]).')
    ap.add_argument('--scenarios', default='all',
                    help='Comma-separated scenario ids (e.g. "1.1,2.3") '
                         'or "all" to run every scenario.')
    ap.add_argument('--methods', default='all',
                    help='Comma-separated method ids, or "all" for the nine '
                         'published defenses. Ablation variants (e.g. '
                         '"mdbg_l0_only,mdbg_rtr15,fed_g2l_25") must be run '
                         'into their own --output_dir, because the scenario '
                         'contract fingerprint covers the method list.')
    ap.add_argument('--config', help='JSON object file with resolved experiment overrides')
    args = ap.parse_args()
    config_overrides = {}
    if args.config:
        with open(args.config, encoding='utf-8') as handle:
            config_overrides = json.load(handle)

    base_output_dir = _ensure_validated_output_dir(args.output_dir)
    os.makedirs(base_output_dir, exist_ok=True)
    _invalidate_master_output(base_output_dir)
    _atomic_write_json(os.path.join(base_output_dir, 'master_progress.json'), {
        'schema_version': SCHEMA_VERSION,
        'complete': False,
        'status': 'validating_selection',
        'valid_scenarios': 0,
        'expected_scenarios': 0,
        'issues': [],
    })

    if args.scenarios != 'all':
        requested = [item.strip() for item in args.scenarios.split(',')]
        if any(not item for item in requested) or len(set(requested)) != len(requested):
            raise BatchContractError('scenario identifiers must be non-empty and unique')
        known = {scenario['id'] for scenario in SCENARIOS}
        unknown = sorted(set(requested) - known)
        if unknown:
            raise BatchContractError(f'unknown scenario identifiers: {unknown}')
        selected = [scenario for scenario in SCENARIOS if scenario['id'] in requested]
    else:
        selected = list(SCENARIOS)
    if not selected:
        raise BatchContractError('at least one scenario must be selected')

    try:
        parsed_seeds = tuple(int(item.strip()) for item in args.seeds.split(','))
    except ValueError as exc:
        raise BatchContractError('seeds must be comma-separated integers') from exc
    if args.methods != 'all':
        requested_methods = [item.strip() for item in args.methods.split(',')]
        if (any(not item for item in requested_methods)
                or len(set(requested_methods)) != len(requested_methods)):
            raise BatchContractError('method ids must be non-empty and unique')
        unknown_methods = sorted(
            set(requested_methods) - set(DEFAULT_EXPERIMENT_CONFIG['method_params'])
        )
        if unknown_methods:
            raise BatchContractError(f'unknown method ids: {unknown_methods}')
        selected_methods = tuple(requested_methods)
    else:
        selected_methods = tuple(METHODS)

    methods_tuple, seeds_tuple = _normalise_matrix(selected_methods, parsed_seeds)
    _atomic_write_json(os.path.join(base_output_dir, 'master_progress.json'), {
        'schema_version': SCHEMA_VERSION,
        'complete': False,
        'status': 'running_scenarios',
        'valid_scenarios': 0,
        'expected_scenarios': len(selected),
        'issues': [],
    })

    start_time = time.time()
    for scenario in selected:
        run_scenario(
            scenario, base_output_dir,
            num_clients=args.num_clients,
            num_rounds=args.num_rounds,
            seeds=seeds_tuple,
            dropout_rate=args.dropout_rate,
            data_size_sigma=args.data_size_sigma,
            dataset=args.dataset,
            methods=methods_tuple,
            config_overrides=config_overrides,
        )

    summaries = _reduce_master(base_output_dir, selected)
    total_time = time.time() - start_time

    # Final cross-scenario console comparison (compact form for 9 methods)
    print("\n" + "=" * 110)
    print("  MASTER COMPARISON: FPR per scenario (lower is better)")
    print("=" * 110)
    short = {
        'fed_mdbscan_g': 'MDBSCAN-G', 'fed_dbscan': 'F-DBSCAN', 'fed_rra': 'F-RRA',
        'fed_g2l': 'F-G2L', 'fedavg': 'FedAvg', 'krum': 'Krum',
        'coord_median': 'CMed', 'fltrust': 'FLTrust', 'flame': 'FLAME',
    }
    header = f"  {'Scenario':<28} " + ' '.join(f"{short[m]:>10}" for m in METHODS)
    print(header)
    print(f"  {'-'*(len(header)-2)}")
    for s in summaries:
        label = s['label'][:26]
        cells = []
        for m in METHODS:
            mm = s['methods'].get(m, {})
            cells.append(f"{mm.get('fpr_mean', float('nan')):>10.4f}"
                         if mm else f"{'-':>10}")
        print(f"  {label:<28} " + ' '.join(cells))

    print(f"\n  Total wall time:  {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  Scenarios done:   {sum(1 for s in summaries if s.get('methods'))}/{len(selected)}")
    print(f"  Output:           {base_output_dir}/")
    print(f"  Master summary:   {os.path.join(base_output_dir, 'master_summary.json')}")
    return 0


def main():
    try:
        return _main()
    except BatchContractError as exc:
        print(f'Batch contract error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
