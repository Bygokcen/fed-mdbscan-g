"""Read-only analysis of the forward-round A/B/C branches.

Reports every readout per dataset, seed and checkpoint round. Nothing is pooled
across datasets: the stratified analysis of the five-step campaign showed that a
single pooled ranking hides opposite behaviour between datasets.

The floor split (clients at exactly ``min_samples_per_client`` versus above it)
is kept separate throughout, because that split -- not a continuous scaling with
data volume -- carries most of the rejection difference in the five-step data.

    .venv/bin/python analysis/forward_round_20260913/analyze.py [run_dir]

Descriptive only: three seeds and correlated rounds do not support a significance
claim, and a single round at a checkpoint is not a learning outcome.
"""

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RESULTS = ROOT / 'new_work/results/mechanism_forward_round'


def latest_run():
    runs = sorted(p for p in RESULTS.glob('forward_*') if (p / 'manifest.json').exists())
    if not runs:
        raise SystemExit('no forward-round run found')
    return runs[-1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rate(hits, total):
    return hits / total if total else None


def median(values):
    return statistics.median(values) if values else None


def summarise_branch(payload, floor):
    """One branch: rejection and geometry, split at the repair floor."""
    record = payload['records'][0]
    metadata = payload['metadata']
    clients = payload['clients']
    rejected = {str(c) for c in record['rejected_ids']}
    l0_accepted = {str(c) for c in payload['shadow']['l0_accepted_ids']}

    groups = {'floor': dict(n=0, rejected=0, l0_rejected=0, norms=[], unique=[], samples=0,
                            accepted_samples=0),
              'above': dict(n=0, rejected=0, l0_rejected=0, norms=[], unique=[], samples=0,
                            accepted_samples=0)}
    for cid in (str(c) for c in record['server_input_ids']):
        count = metadata['client_metadata'][cid]['sample_count']
        bucket = groups['floor' if count <= floor else 'above']
        bucket['n'] += 1
        bucket['samples'] += count
        if cid in rejected:
            bucket['rejected'] += 1
        else:
            bucket['accepted_samples'] += count
        if cid not in l0_accepted:
            bucket['l0_rejected'] += 1
        norm = record['update_norms'].get(cid)
        if norm is not None:
            bucket['norms'].append(norm)
        bucket['unique'].append(clients[cid][-1]['unique_examples_so_far'])

    total_samples = sum(g['samples'] for g in groups.values())
    accepted_samples = sum(g['accepted_samples'] for g in groups.values())
    out = dict(
        accuracy=record['accuracy'],
        fpr=record['fpr'],
        rejected=len(rejected),
        l0_rejected=len(record['server_input_ids']) - len(l0_accepted),
        accepted_sample_share=rate(accepted_samples, total_samples),
    )
    for name, g in groups.items():
        out[f'{name}_n'] = g['n']
        out[f'{name}_fpr'] = rate(g['rejected'], g['n'])
        out[f'{name}_l0_fpr'] = rate(g['l0_rejected'], g['n'])
        out[f'{name}_median_norm'] = median(g['norms'])
        out[f'{name}_median_unique_examples'] = median(g['unique'])
    return out


def main():
    run = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else latest_run()
    manifest = json.loads((run / 'manifest.json').read_text())
    status = json.loads((run / 'status.json').read_text())

    rows, sources = [], {}
    for dataset in manifest['datasets']:
        for seed in manifest['seeds']:
            config = json.loads(
                (run / f'configs/{dataset}_{seed}_branch.json').read_text())
            floor = config['min_samples_per_client']
            for checkpoint_round in manifest['checkpoint_rounds']:
                for arm in manifest['arms']:
                    path = run / f'branches/{dataset}_{seed}_r{checkpoint_round:03d}_{arm}.json'
                    if not path.exists():
                        continue
                    payload = json.loads(path.read_text())
                    if payload['outcome'] != 'completed':
                        continue
                    sources[str(path.relative_to(run))] = sha256(path)
                    rows.append(dict(dataset=dataset, seed=seed, round=checkpoint_round,
                                     arm=arm, **summarise_branch(payload, floor)))

    fields = list(rows[0]) if rows else []
    with (HERE / 'branches.csv').open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in rows:
            handle.write(','.join('' if row[f] is None else str(row[f]) for f in fields) + '\n')

    # Per dataset and round: the arm contrast the design was built to read.
    contrast = []
    for dataset in manifest['datasets']:
        for checkpoint_round in manifest['checkpoint_rounds']:
            cell = [r for r in rows if r['dataset'] == dataset and r['round'] == checkpoint_round]
            if not cell:
                continue
            item = dict(dataset=dataset, round=checkpoint_round,
                        seeds=len({r['seed'] for r in cell}))
            for arm in manifest['arms']:
                arm_rows = [r for r in cell if r['arm'] == arm]
                item[f'{arm}_fpr'] = median([r['fpr'] for r in arm_rows])
                item[f'{arm}_floor_fpr'] = median(
                    [r['floor_fpr'] for r in arm_rows if r['floor_fpr'] is not None])
                item[f'{arm}_above_fpr'] = median(
                    [r['above_fpr'] for r in arm_rows if r['above_fpr'] is not None])
                item[f'{arm}_floor_norm'] = median(
                    [r['floor_median_norm'] for r in arm_rows if r['floor_median_norm'] is not None])
                item[f'{arm}_above_norm'] = median(
                    [r['above_median_norm'] for r in arm_rows if r['above_median_norm'] is not None])
                item[f'{arm}_accuracy'] = median([r['accuracy'] for r in arm_rows])
            contrast.append(item)

    fields = list(contrast[0]) if contrast else []
    with (HERE / 'by_round.csv').open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in contrast:
            handle.write(','.join('' if row[f] is None else str(row[f]) for f in fields) + '\n')

    summary = dict(
        run=str(run.relative_to(ROOT)),
        state=status['state'],
        completed=status['completed'],
        total=status['total'],
        branches_analysed=len(rows),
        expected_branches=manifest['expected_branches'],
        checkpoint_rounds=manifest['checkpoint_rounds'],
        by_dataset_and_round=contrast,
    )
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (HERE / 'provenance.json').write_text(json.dumps(dict(
        read_only=True, run=str(run.relative_to(ROOT)),
        analysis_sha256=sha256(__file__), inputs=sources), indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'by_dataset_and_round'},
                     indent=2))


if __name__ == '__main__':
    main()
