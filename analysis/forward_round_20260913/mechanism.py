"""Read-only mechanism analysis behind the forward-round branches.

Two questions the branch summary alone cannot answer.

1. Why do above-floor clients produce larger updates once training has started?
   The branch traces record the loss of every mini-batch, so the loss a client
   *arrives* at a round with can be separated from the loss it leaves with.

2. Is that divergence produced by the filter, or is it already present without
   any filtering? The completed five-step campaign contains a uniform-mean arm
   that never rejects anyone, under the same partition, seeds and step budget,
   so the two trajectories can be compared round by round.

    .venv/bin/python analysis/forward_round_20260913/mechanism.py [run_dir]

Descriptive only. The uniform-mean comparison is between two runs that follow
different global trajectories by construction; it bounds the filter's
contribution, it does not isolate it within a single run.
"""

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RESULTS = ROOT / 'new_work/results/mechanism_forward_round'
STEPS5 = ROOT / 'new_work/results/step_control/steps5_20260913/runs/step_control_5'

DATASETS = ['mnist', 'fashion_mnist', 'har']
SEEDS = [42, 137, 2024]
NORM_ROUNDS = [0, 5, 10, 20, 29]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def latest_run():
    runs = sorted(p for p in RESULTS.glob('forward_*') if (p / 'manifest.json').exists())
    if not runs:
        raise SystemExit('no forward-round run found')
    return runs[-1]


def arrival_loss(run, manifest, sources):
    """Loss at the first and last local step, split at the repair floor."""
    rows = []
    for dataset in DATASETS:
        floor = json.loads(
            (run / f'configs/{dataset}_{SEEDS[0]}_branch.json').read_text()
        )['min_samples_per_client']
        for checkpoint_round in manifest['checkpoint_rounds']:
            groups = {'floor': dict(first=[], last=[]), 'above': dict(first=[], last=[])}
            for seed in SEEDS:
                path = run / f'branches/{dataset}_{seed}_r{checkpoint_round:03d}_A.json'
                if not path.exists():
                    continue
                sources[str(path.relative_to(run))] = sha256(path)
                payload = json.loads(path.read_text())
                meta = payload['metadata']['client_metadata']
                for cid, steps in payload['clients'].items():
                    losses = [s['batch_loss'] for s in steps if 'batch_loss' in s]
                    if len(losses) < 2:
                        continue
                    bucket = groups['floor' if meta[cid]['sample_count'] <= floor else 'above']
                    bucket['first'].append(losses[0])
                    bucket['last'].append(losses[-1])
            if not groups['floor']['first']:
                continue
            rows.append(dict(
                dataset=dataset, round=checkpoint_round,
                floor_first_loss=statistics.median(groups['floor']['first']),
                floor_last_loss=statistics.median(groups['floor']['last']),
                above_first_loss=statistics.median(groups['above']['first']),
                above_last_loss=statistics.median(groups['above']['last'])))
    return rows


def norm_ratio_with_and_without_filtering(sources):
    """Above-floor over floor update norm, per round, for a rejecting and a
    non-rejecting aggregator trained under the same partition and seeds."""
    rows = []
    for dataset in DATASETS:
        for method in ['fedavg', 'fed_mdbscan_g']:
            per_round = {}
            for seed in SEEDS:
                path = STEPS5 / dataset / 'scenario_6.2/runs' / f'{method}_seed{seed}.json'
                if not path.exists():
                    continue
                sources[str(path.relative_to(ROOT))] = sha256(path)
                payload = json.loads(path.read_text())
                meta = payload['run_metadata']['client_metadata']
                for record in payload['records']:
                    floor_norms, above_norms = [], []
                    for cid in (str(c) for c in record['server_input_ids']):
                        norm = record['update_norms'].get(cid)
                        if norm is None:
                            continue
                        (floor_norms if meta[cid]['sample_count'] <= 20
                         else above_norms).append(norm)
                    if floor_norms and above_norms:
                        per_round.setdefault(record['round'], []).append(
                            statistics.median(above_norms) / statistics.median(floor_norms))
            if per_round:
                rows.append(dict(dataset=dataset, method=method, **{
                    f'round_{r}': (statistics.median(per_round[r]) if r in per_round else None)
                    for r in NORM_ROUNDS}))
    return rows


def write_csv(path, rows):
    if not rows:
        return
    fields = list(rows[0])
    with Path(path).open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in rows:
            handle.write(','.join(
                '' if row[f] is None else str(row[f]) for f in fields) + '\n')


def main():
    run = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else latest_run()
    manifest = json.loads((run / 'manifest.json').read_text())
    sources = {}

    losses = arrival_loss(run, manifest, sources)
    ratios = norm_ratio_with_and_without_filtering(sources)
    write_csv(HERE / 'arrival_loss.csv', losses)
    write_csv(HERE / 'norm_ratio_by_aggregator.csv', ratios)

    summary = dict(run=str(run.relative_to(ROOT)),
                   arrival_loss=losses, norm_ratio=ratios,
                   norm_ratio_rounds=NORM_ROUNDS)
    (HERE / 'mechanism.json').write_text(json.dumps(summary, indent=2) + '\n')
    (HERE / 'mechanism_provenance.json').write_text(json.dumps(dict(
        read_only=True, analysis_sha256=sha256(__file__), inputs=sources), indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
