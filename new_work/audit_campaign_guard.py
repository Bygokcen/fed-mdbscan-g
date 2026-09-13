"""External validation for immutable audit-v2 campaigns; never modifies evidence."""
import json
from pathlib import Path


def validate_science(unit):
    from simulation.contracts import build_participation_schedule
    from simulation.run_batch_experiments import _sha256_json, BatchContractError
    from simulation.metrics import evaluate_attack_alert
    c, meta = unit['resolved_config'], unit['run_metadata']
    def require(ok, reason):
        if not ok:
            raise BatchContractError(reason)
    active = meta['active_client_ids']
    require(all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < c['num_clients'] for i in active), 'active IDs')
    latent, schedule = build_participation_schedule(c, active)
    require(meta['participation_schedule'] == schedule, 'participation schedule')
    require(meta['latent_malicious_ids'] == latent, 'latent attacker assignment')
    require(meta['schedule_sha256'] == _sha256_json(schedule), 'schedule hash')
    after = meta['partition_repair']['after_counts']
    require(sorted(int(i) for i, n in after.items() if n > 0) == sorted(active), 'active partition counts')
    if c['partition_policy'] == 'repair_minimum':
        require(len(active) == c['num_clients'] and min(after.values()) >= c['min_samples_per_client'], 'minimum partition floor')
    metadata = meta['client_metadata']
    for cid in active:
        info = metadata[str(cid)]
        require(info['sample_count'] == after[str(cid)] == sum(info['class_histogram'].values()), 'client sample counts')
    for r in unit['records']:
        rid = r['round']
        truth = set(latent) if (c['attack_mode'] != 'clean' and rid >= c['attack_start_round'] and
                   (c['attack_end_round'] is None or rid < c['attack_end_round'])) else set()
        excluded = truth if c['attack_mode'] == 'oracle' else set()
        require(set(r['actual_malicious_ids']) == truth, 'attack mode/window')
        require(r['participant_ids'] == r['scheduled_ids'] == schedule[rid], 'round participants')
        require(r['update_ids'] == [f'{rid}:{cid}' for cid in schedule[rid]], 'update identities')
        require(set(r['oracle_excluded_ids']) == excluded, 'oracle exclusions')
        require(set(r['server_input_ids']) == set(schedule[rid]) - excluded, 'server inputs')
        rho = len(truth) / len(schedule[rid])
        require(rho <= c['malicious_ratio'] + 1e-12 and abs(r['effective_malicious_ratio']-rho) < 1e-12, 'configured attack ratio')
        require(r['attack_active'] == int(bool(truth)), 'attack presence')
        groups = {}
        for cid in set(schedule[rid]) - truth:
            for dim in ['size_quartile', 'dominant_label']:
                name = f'{dim}:{metadata[str(cid)][dim]}'
                counts = groups.setdefault(name, {'fp': 0, 'tn': 0})
                counts['fp' if cid in r['rejected_ids'] else 'tn'] += 1
        require(groups == r['group_confusion'], 'benign group confusion')
        alerts = evaluate_attack_alert(r, truth, r['attack_alert'])
        require(all(r[k] == v for k, v in alerts.items()), 'alert confusion')
        if c['attack_type'] == 'patch_backdoor':
            hits, n = r['backdoor_target_hits'], r['backdoor_test_count']
            require(isinstance(hits, int) and isinstance(n, int) and 0 <= hits <= n and n > 0, 'backdoor denominator')
            require(abs(r['backdoor_asr'] - hits/n) < 1e-12, 'backdoor ASR')


def check_job(root, job, manifest):
    from simulation.run_audit_campaign import job_config
    from simulation.run_batch_experiments import _read_valid_unit, _sha256_json
    config = job_config(root, job)
    base = Path(config['output_dir'])
    result = dict(job=job['id'], valid=0, missing=[], failures=[], invalid=[], identities=[])
    expected = {f'{method}_seed{seed}.json' for method in job['methods'] for seed in job['seeds']}
    for p in (base / 'runs').glob('*.json'):
        if p.name not in expected:
            result['invalid'].append({'path': str(p), 'reason': 'unexpected unit filename'})
    for method in job['methods']:
        for seed in job['seeds']:
            name = f'{method}_seed{seed}.json'
            path = base / 'runs' / name
            try:
                if path.exists():
                    unit = _read_valid_unit(path, job['scenario']['id'], method, seed, config)
                    validate_science(unit)
                    meta = unit['run_metadata']
                    if meta['dataset_identity'] != manifest['dataset_identities'][job['dataset']]:
                        raise ValueError('dataset identity differs from manifest')
                    result['valid'] += 1
                    result['identities'].append(dict(seed=seed, identity=[meta[k] for k in
                        ['partition_sha256', 'initial_model_sha256', 'schedule_sha256']]))
                else:
                    failure = base / 'failures' / name
                    if failure.exists():
                        f = json.loads(failure.read_text());unsigned = dict(f);digest = unsigned.pop('payload_sha256')
                        if digest != _sha256_json(unsigned) or f['method'] != method or f['seed'] != seed or f['protocol_digest'] != config['protocol_digest']:
                            raise ValueError('failure evidence identity/checksum')
                        result['failures'].append({'path': str(failure), 'reason': f['reason'], 'method': method, 'seed': seed})
                    else:
                        result['missing'].append(name)
            except Exception as exc:
                result['invalid'].append({'path': str(path), 'reason': str(exc)})
    return result


def audit_campaign(root, manifest):
    results = [check_job(root, job, manifest) for job in manifest['jobs']]
    identities = {}
    for job, result in zip(manifest['jobs'], results):
        phase = 'paired' if job['phase'] in ['main', 'clean', 'oracle', 'ablation'] else job['phase']
        for row in result.pop('identities'):
            key = (phase, job['dataset'], job['scenario']['id'], row['seed'])
            if identities.setdefault(key, row['identity']) != row['identity']:
                result['invalid'].append({'reason': 'paired identity mismatch', 'seed': row['seed']})
    valid = sum(r['valid'] for r in results)
    return dict(complete=valid == manifest['expected_units'] and not any(r['invalid'] for r in results),
                valid_units=valid, expected_units=manifest['expected_units'], jobs=results,
                failed_units=sum(len(r['failures']) for r in results),
                missing_units=sum(len(r['missing']) for r in results),
                invalid_units=sum(len(r['invalid']) for r in results))
