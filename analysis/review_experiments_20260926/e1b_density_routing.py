#!/usr/bin/env python3
"""Exploratory check, not pre-specified in PROTOCOL.md: where do copied attackers land?

The manuscript's density discussion relied on a one-dimensional toy input, on which
exactly duplicated points have a zero nearest-neighbour distance sum and receive the
implementation's fallback density of 1.  This script measures what the frozen density
function does on the recorded high-dimensional update matrices of the constrained
probes, where every attacker submits a bit-identical copy of one vector:

  * the five-step development matrices of Section VIII (Min-Max, 18 attackers), read
    with the development study's frozen source;
  * the canonical checkpoint matrices re-executed in E1 (Min-Max alpha=0.1 and Min-Sum
    alpha=0.01, 27 attackers), read with the canonical frozen source.

For each matrix it records whether the attacker rows are bit-identical, the attackers'
nearest-neighbour distance sums and relative densities, the largest honest density,
and the split of the low-density set at the implementation's own threshold.
Writes e1b_density_routing.csv and e1b_density_routing.json next to this script.
"""
import os
for _v in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[_v] = '1'
import csv
import hashlib
import importlib.util
import json
import pathlib

import numpy as np

ROOT = pathlib.Path('/home/gokcen/Fed_MDBSCAN_TIFS/new_work/results')
DEV_SRC = ROOT / 'cutoff_development/study_20260914_v1/source/new_work/simulation/mdbscan.py'
CANON_SRC = ROOT / 'validated/audit-v2/full_20260910/source/new_work/simulation/mdbscan.py'
GATE = ROOT / 'mechanism_gate_replay/replay_20260915_v2'
REVIEW = ROOT / 'review_20260926/units'
HERE = pathlib.Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def measure(mod, matrix, participants, malicious, meta, rows, inputs, paths):
    from sklearn.neighbors import NearestNeighbors
    for p in paths:
        inputs[str(p)] = sha(p)
    ai = [i for i, p in enumerate(participants) if p in malicious]
    hi = [i for i, p in enumerate(participants) if p not in malicious]
    identical = all(np.array_equal(matrix[i], matrix[ai[0]]) for i in ai)
    k = min(5, len(matrix) - 1)
    distances, _ = NearestNeighbors(n_neighbors=k + 1, metric='euclidean').fit(matrix).kneighbors(matrix)
    sums = distances[:, 1:].sum(axis=1)
    rd = mod.compute_relative_density(matrix, 5)
    t, gap, _ = mod._auto_estimate_t(rd, 10.0)
    rows.append(dict(**meta, attackers=len(ai), honest=len(hi), attackers_bit_identical=bool(identical),
                     attacker_distance_sum_min=float(sums[ai].min()), attacker_distance_sum_max=float(sums[ai].max()),
                     attacker_zero_sum=int((sums[ai] == 0).sum()),
                     attacker_rd_min=float(rd[ai].min()), honest_rd_max=float(rd[hi].max()),
                     density_gap=bool(gap), threshold=float(t),
                     low_density_attackers=int((rd[ai] < t).sum()), low_density_honest=int((rd[hi] < t).sum())))


def main():
    rows, inputs = [], {}
    dev = module(DEV_SRC, 'dev_mdbscan')
    canon = module(CANON_SRC, 'canon_mdbscan')
    inputs[str(DEV_SRC)] = sha(DEV_SRC)
    inputs[str(CANON_SRC)] = sha(CANON_SRC)
    plan = json.loads((GATE / 'plan.json').read_text())
    for idx, ref in enumerate(plan['references']):
        if 'scenario_cut_minmax' not in ref['path'] or 'cutoff_attacked' not in ref['path']:
            continue
        d = GATE / f'ref_{idx:02d}'
        branches = json.loads((d / 'branches.json').read_text())
        for r in (0, 9, 29):
            st_path, x_path = d / f'round_{r:02d}_state.json', d / f'round_{r:02d}_updates.npy'
            state = json.loads(st_path.read_text())
            b = next(x for x in branches if x['round'] == r)
            measure(dev, np.load(x_path), state['participants'], set(b['actual_malicious_ids']),
                    dict(source='five-step development', reference=ref['path'], round=r), rows, inputs,
                    (st_path, x_path, d / 'branches.json'))
    for unit in sorted(REVIEW.glob('E1_*_7.[12]_*')):
        records = json.loads((unit / 'records.json').read_text())['records']
        for r in (0, 9, 29):
            st_path, x_path = unit / f'round_{r:02d}_state.json', unit / f'round_{r:02d}_updates.npy'
            state = json.loads(st_path.read_text())
            measure(canon, np.load(x_path), state['participants'], set(records[r]['actual_malicious_ids']),
                    dict(source='canonical', reference=unit.name, round=r), rows, inputs,
                    (st_path, x_path, unit / 'records.json'))
    with open(HERE / 'e1b_density_routing.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = {}
    for src in ('five-step development', 'canonical'):
        rs = [r for r in rows if r['source'] == src]
        summary[src] = dict(matrices=len(rs), bit_identical=sum(r['attackers_bit_identical'] for r in rs),
                            attacker_zero_sums=sum(r['attacker_zero_sum'] for r in rs),
                            attacker_rd_min=min(r['attacker_rd_min'] for r in rs),
                            honest_rd_max=max(r['honest_rd_max'] for r in rs),
                            density_gap=sum(r['density_gap'] for r in rs),
                            low_density_attackers=sum(r['low_density_attackers'] for r in rs),
                            low_density_honest=sum(r['low_density_honest'] for r in rs),
                            honest_total=sum(r['honest'] for r in rs))
    out = dict(description=__doc__.strip().splitlines()[0], summary=summary,
               script_sha256=sha(__file__), inputs_sha256=inputs)
    (HERE / 'e1b_density_routing.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
