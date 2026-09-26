#!/usr/bin/env python3
"""E0 of PROTOCOL.md: what the cluster stage did in every canonical Fed-MDBSCAN-G round.

Read only.  For each round of the 201 canonical Fed-MDBSCAN-G runs (main phase) the
recorded fields give the Stage-1 pool size |B0| = n - l0_rejected_count and the final
accepted set B.  Because B is always a subset of B0, |B0| - |B| is the number of
Stage-1-accepted updates that the cluster stage removed.  In adversary-free rounds
every removed update is honest.

Writes, next to this script:
    e0_stage_counts.csv    one row per (attack family, dataset, alpha)
    e0_summary.json        pooled rows used by the supplement table, plus provenance
"""
import csv
import hashlib
import json
import pathlib
from collections import defaultdict

CANON = pathlib.Path('/home/gokcen/Fed_MDBSCAN_TIFS/new_work/results/validated/audit-v2/full_20260910')
HERE = pathlib.Path(__file__).resolve().parent
FAMILY = {'minmax_omniscient': 'constrained', 'minsum_omniscient': 'constrained',
          'patch_backdoor': 'patch', 'gaussian': 'loud_gaussian', 'label_flip': 'label_flip',
          'stealth_gaussian': 'bounded', 'adaptive_gaussian': 'bounded'}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main():
    files = sorted((CANON / 'runs/main').glob('*/*/runs/fed_mdbscan_g_seed*.json'))
    assert len(files) == 201, len(files)
    cells = defaultdict(lambda: defaultdict(int))
    inputs = {}
    for path in files:
        inputs[str(path.relative_to(CANON))] = sha(path)
        run = json.loads(path.read_text())
        config = run['resolved_config']
        attacked = config.get('malicious_ratio', 0) > 0
        family = FAMILY[config['attack_type']] if attacked else 'clean'
        key = (family, config['dataset'], config['non_iid_alpha'])
        for r in run['records']:
            c = cells[key]
            n, l0 = r['n_participants'], r['l0_rejected_count']
            accepted = set(r['accepted_ids'])
            b0_size = n - l0
            removed = b0_size - len(accepted)
            assert removed >= 0, 'B must be a subset of B0'
            c['runs_rounds'] += 1
            c['gate_open'] += int(r['layer_used'] != 'L0_only')
            c['valve_rounds'] += int(r['fallback_applied'])
            c['rounds_with_removal'] += int(removed > 0)
            c['removed_updates'] += removed
            c['honest_rejections'] += r['fp']
            c['attacker_rejections'] += r['tp']
            if not attacked:
                assert r['tp'] == 0 and not r['actual_malicious_ids']
    rows = []
    for (family, dataset, alpha), c in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[0][2])):
        rows.append(dict(family=family, dataset=dataset, alpha=alpha, rounds=c['runs_rounds'],
                         gate_open=c['gate_open'], valve_rounds=c['valve_rounds'],
                         rounds_with_removal=c['rounds_with_removal'], removed_updates=c['removed_updates'],
                         honest_rejections=c['honest_rejections'], attacker_rejections=c['attacker_rejections']))
    with open(HERE / 'e0_stage_counts.csv', 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    pooled = defaultdict(lambda: defaultdict(int))
    for row in rows:
        k = (row['family'], row['alpha'])
        for f in ('rounds', 'gate_open', 'rounds_with_removal', 'removed_updates', 'honest_rejections'):
            pooled[k][f] += row[f]
        pooled[k]['datasets'] += 1
    summary = dict(
        description=__doc__.strip().splitlines()[0],
        pooled=[dict(family=f, alpha=a, **v) for (f, a), v in sorted(pooled.items(), key=lambda kv: (kv[0][0], -kv[0][1]))],
        clean_alpha001_removed_share_of_honest_rejections={
            row['dataset']: round(row['removed_updates'] / row['honest_rejections'], 4)
            for row in rows if row['family'] == 'clean' and row['alpha'] == 0.01},
        runs=len(files), script_sha256=sha(__file__), inputs_sha256=inputs)
    (HERE / 'e0_summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    for row in rows:
        print(row)


if __name__ == '__main__':
    main()
