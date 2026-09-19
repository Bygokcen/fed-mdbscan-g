"""Evaluate the flat-profile de-inflation matrix against PROTOCOL.md.

Two measures are reported together, as the protocol fixed in advance: whether the
trend signal still separates the attackers, and what the attack gives up to get
there. The trend statistic is imported from the temporal probe so both use one
code path.

    .venv/bin/python analysis/temporal_deinflation_20260919/analyze.py [run_dir]
"""

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path('/home/gokcen/Fed_MDBSCAN_TIFS')
HERE = Path(__file__).resolve().parent
FLAT_BASE = ROOT / 'new_work/results/temporal_deinflation'
DEV = ROOT / 'new_work/results/cutoff_development/study_20260914_v1/runs'

DATASETS = ['mnist', 'fashion_mnist']
SEEDS = [42, 137, 2024]
METHODS = ['fedavg', 'fed_mdbscan_g']
RATIOS = [1.0, 2.0]

_spec = importlib.util.spec_from_file_location(
    'temporal_probe', ROOT / 'analysis/temporal_signature_20260919/run_probe.py')
temporal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(temporal)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def latest_run():
    runs = sorted(p for p in FLAT_BASE.glob('flat_*') if (p / 'manifest.json').exists())
    if not runs:
        raise SystemExit('no flat-profile run found')
    return runs[-1]


def trend_auc(payload, marked_ids):
    """Same statistic and code path as the temporal signature probe."""
    stats = temporal.client_series(payload)
    marked = {str(c) for c in marked_ids}
    positive = [s['trend'] for c, s in stats.items() if c in marked and s['trend'] is not None]
    negative = [s['trend'] for c, s in stats.items()
                if c not in marked and s['trend'] is not None]
    return temporal.auc(positive, negative)


def attack_diagnostics(payload):
    """Constraint measurements recorded by the attack itself, per round."""
    violations = clamped = rounds = 0
    ratios = []
    for record in payload['records']:
        diagnostics = record.get('attack_diagnostics') or {}
        if not diagnostics:
            continue
        info = next(iter(diagnostics.values()))
        rounds += 1
        if info.get('constraint_achieved') is not None:
            bound = info['constraint_bound']
            if info['constraint_achieved'] > bound + max(1e-10, abs(bound) * 1e-5):
                violations += 1
        if info.get('gamma_clamped'):
            clamped += 1
        if info.get('realized_norm') and info.get('target_norm'):
            ratios.append(info['realized_norm'] / info['target_norm'])
    return dict(attack_rounds=rounds, constraint_violations=violations,
                gamma_clamped_rounds=clamped,
                realized_over_target_median=(
                    round(statistics.median(ratios), 4) if ratios else None))


def main():
    run = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else latest_run()
    manifest = json.loads((run / 'manifest.json').read_text())
    status = json.loads((run / 'status.json').read_text())

    rows, sources, identity_failures = [], {}, []
    for dataset in DATASETS:
        for seed in SEEDS:
            for method in METHODS:
                original = (DEV / f'cutoff_attacked/{dataset}/scenario_cut_minmax'
                            / f'runs/{method}_seed{seed}.json')
                clean = (DEV / f'cutoff_clean/{dataset}/scenario_cut_minmax'
                         / f'runs/{method}_seed{seed}.json')
                if not original.exists() or not clean.exists():
                    continue
                original_payload = json.loads(original.read_text())
                clean_payload = json.loads(clean.read_text())
                sources[str(original.relative_to(ROOT))] = sha256(original)
                sources[str(clean.relative_to(ROOT))] = sha256(clean)

                attackers = original_payload['records'][0]['actual_malicious_ids']
                clean_accuracy = clean_payload['records'][-1]['accuracy']
                reference = dict(
                    dataset=dataset, seed=seed, method=method, variant='minmax_budget',
                    ratio=None,
                    trend_auc=trend_auc(original_payload, attackers),
                    final_accuracy=original_payload['records'][-1]['accuracy'],
                    clean_accuracy=clean_accuracy,
                    **attack_diagnostics(original_payload))
                reference['damage'] = clean_accuracy - reference['final_accuracy']
                rows.append(reference)

                for ratio in RATIOS:
                    cell = run / 'cells' / f'{dataset}_{seed}_r{ratio}_{method}.json'
                    if not cell.exists():
                        continue
                    payload = json.loads(cell.read_text())
                    if payload['outcome'] != 'completed':
                        continue
                    sources[str(cell.relative_to(ROOT))] = sha256(cell)
                    meta, original_meta = payload['run_metadata'], original_payload['run_metadata']
                    for key in ('partition_sha256', 'initial_model_sha256', 'schedule_sha256'):
                        if meta[key] != original_meta[key]:
                            identity_failures.append(
                                f'{dataset}/{seed}/{method}/r{ratio}: {key}')
                    item = dict(
                        dataset=dataset, seed=seed, method=method, variant='minmax_flat',
                        ratio=ratio,
                        trend_auc=trend_auc(payload, attackers),
                        final_accuracy=payload['records'][-1]['accuracy'],
                        clean_accuracy=clean_accuracy,
                        **attack_diagnostics(payload))
                    item['damage'] = clean_accuracy - item['final_accuracy']
                    rows.append(item)

    if identity_failures:
        raise SystemExit('identity mismatch: ' + '; '.join(identity_failures))

    fields = list(rows[0])
    with (HERE / 'per_cell.csv').open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in rows:
            handle.write(','.join('' if row[f] is None else str(row[f]) for f in fields) + '\n')

    summary = []
    for method in METHODS:
        for variant, ratio in [('minmax_budget', None)] + [('minmax_flat', r) for r in RATIOS]:
            cell = [r for r in rows if r['method'] == method
                    and r['variant'] == variant and r['ratio'] == ratio]
            if not cell:
                continue
            aucs = [r['trend_auc'] for r in cell if r['trend_auc'] is not None]
            summary.append(dict(
                method=method, variant=variant, ratio=ratio, runs=len(cell),
                trend_auc_median=round(statistics.median(aucs), 4) if aucs else None,
                trend_auc_min=round(min(aucs), 4) if aucs else None,
                trend_auc_max=round(max(aucs), 4) if aucs else None,
                damage_median=round(statistics.median(r['damage'] for r in cell), 4),
                final_accuracy_median=round(
                    statistics.median(r['final_accuracy'] for r in cell), 4),
                constraint_violations=sum(r['constraint_violations'] for r in cell),
                gamma_clamped_rounds=sum(r['gamma_clamped_rounds'] for r in cell),
                attack_rounds=sum(r['attack_rounds'] for r in cell)))

    fields = list(summary[0])
    with (HERE / 'summary_by_variant.csv').open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in summary:
            handle.write(','.join('' if row[f] is None else str(row[f]) for f in fields) + '\n')

    report = dict(run=str(run.relative_to(ROOT)), state=status['state'],
                  cells=status['completed'], identity_checks_passed=True,
                  protocol_sha256=manifest['protocol_sha256'], by_variant=summary)
    (HERE / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'provenance.json').write_text(json.dumps(dict(
        read_only=True, run=str(run.relative_to(ROOT)),
        script_sha256=sha256(__file__),
        protocol_sha256=sha256(HERE / 'PROTOCOL.md'), inputs=sources), indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'by_variant'}, indent=2))


if __name__ == '__main__':
    main()
