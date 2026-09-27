#!/usr/bin/env python3
"""measure_gamma.py -- measure the radial dispersion ratio Gamma(B_0) that
Proposition 3 of the v3 manuscript is conditional on.

WHY THIS EXISTS
    Proposition 3 states: if
        Gamma(B_0) = max_{i in B_0} ||u_i - m_{B_0}||  /  median_{i in B_0} ||u_i - m_{B_0}||
    is at most the consensus threshold tau, then NO subset of the stage-1 accepted
    pool can be rejected by the cluster-consensus test, so the clustering stage is
    provably inert.  The manuscript currently reports outcomes that are CONSISTENT
    with this condition (no cluster rejection on any attacked checkpoint; the
    admitted set unchanged in all 144 gate comparisons) but does not measure the
    condition itself.  This script measures it.

WHAT IT IS NOT
    Not a training run.  Not a GPU job.  No simulation, no new campaign, no
    package installation.  It re-reads the same frozen update matrices that
    analysis/unclustered_policy_20260920/analyze.py already reads, recomputes the
    stage-1 geometric median with the same frozen function, and reduces it to one
    scalar per checkpoint.  Runtime is dominated by the Weiszfeld iterations and
    should be minutes, not hours.

STATUS
    Written against the code paths of analyze.py (same archive layout, same frozen
    module, same tracing hook).  It has NOT been executed against the raw archive,
    which lives only on the project machine.  It fails closed: any hash mismatch,
    missing file or non-finite value raises rather than producing a partial table.
    Check the first printed reference before letting it run to completion.

USAGE (on the project machine, from the repository root)
    .venv/bin/python analysis/measure_gamma.py --root "$PWD" --output /tmp/gamma_v1

    --output must not already exist.
"""
from __future__ import annotations

import os
for _k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[_k] = '1'

import argparse
import csv
import hashlib
import importlib.util
import inspect
import json
import statistics as st
import sys
import traceback
from pathlib import Path

import numpy as np

# --- paths inside the project repository (identical to analyze.py) -----------
STUDY = 'new_work/results/cutoff_development/study_20260914_v1'
GATE = 'new_work/results/mechanism_gate_replay/replay_20260915_v2'
FORWARD = 'new_work/results/mechanism_forward_round/forward_20260913_201632'
ABC = 'new_work/results/mechanism_cluster_replay/replay_20260914'
POLICY_SCRIPT = 'analysis/unclustered_policy_20260920/analyze.py'

ROUNDS = (0, 9, 29)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def require(ok, label):
    if not ok:
        raise RuntimeError(label)


def module_at(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gamma_of(mod, matrix, b0, tau):
    """Radial dispersion ratio of the stage-1 accepted pool.

    Uses the frozen Weiszfeld implementation so that the centre is exactly the
    one the consensus test would have used.  Returns a dict of scalars.
    """
    ordered = sorted(b0)
    require(len(ordered) > 0, 'empty B0')
    trusted = matrix[ordered]
    centre = np.asarray(mod._weiszfeld_geometric_median(trusted), dtype=float)
    radii = np.linalg.norm(trusted - centre, axis=1)
    require(np.isfinite(radii).all(), 'non-finite radius')
    med = float(np.median(radii))
    mx = float(radii.max())
    # The implementation floors the median radius at 1e-10 before scaling.
    floored = max(med, 1e-10)
    gamma = mx / floored
    return {
        'b0_size': len(ordered),
        'radius_max': mx,
        'radius_median': med,
        'radius_min': float(radii.min()),
        'radius_p90': float(np.percentile(radii, 90)),
        'gamma': gamma,
        'tau': tau,
        # Proposition 3's hypothesis.  True => the consensus test provably
        # cannot reject ANY subset of B0 at this checkpoint.
        'vacuous': bool(gamma <= tau),
        'median_floored': bool(med < 1e-10),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)

    inputs, rows = {}, []

    def record(path):
        inputs[str(Path(path).relative_to(root))] = sha(path)

    def load(path):
        record(path)
        return json.loads(Path(path).read_text())

    def verify(path, digest):
        record(path)
        require(sha(path) == digest, 'hash mismatch: ' + str(path))

    try:
        study, gate = root / STUDY, root / GATE
        policy = module_at(root / POLICY_SCRIPT, 'policy_helpers')
        record(root / POLICY_SCRIPT)

        plan = load(gate / 'plan.json')
        verify(gate / 'observer.py', plan['observer_sha256'])
        for name, h in plan['provenance']['snapshot_files'].items():
            verify(study / 'source' / name, h)
        mod = module_at(study / 'source/new_work/simulation/mdbscan.py', 'gate_frozen')

        # density-only gate variant, built exactly as analyze.py builds it
        src = inspect.getsource(mod.fed_mdbscan_g_filter)
        target = 'attack_gate = bool(density_gap_detected and l0_supports_attack)'
        require(src.count(target) == 1, 'unique gate replacement')
        ns = dict(mod.__dict__)
        exec(compile(src.replace(target, 'attack_gate = bool(density_gap_detected)'),
                     '<density-only-copy>', 'exec'), ns)
        forced = ns['fed_mdbscan_g_filter']

        def evaluate(module, fn, matrix, params, ids, malicious, meta):
            require(len(ids) == len(matrix) and len(set(ids)) == len(ids), 'ID mapping')
            require(np.isfinite(matrix).all(), 'finite input')
            _result, g = policy.traced(fn, matrix, params)
            b0 = set(g['l0_benign'])
            clusters = g.get('natural_clusters', [])
            rejected = set(g.get('rejected_snnc_indices', []))
            tau = float(params.get('consensus_threshold', 2.0))
            row = dict(**meta,
                       n=len(ids),
                       partition_executed=bool('low_indices' in g),
                       n_clusters=len(clusters),
                       n_cluster_rejected_members=len(rejected),
                       any_cluster_rejected=bool(rejected),
                       malicious_count=len(set(malicious)))
            row.update(gamma_of(module, matrix, b0, tau))
            # Proposition 3 is falsified at this checkpoint if the test fired
            # while the hypothesis held.  This must never happen.
            require(not (row['vacuous'] and row['any_cluster_rejected']),
                    'PROPOSITION 3 VIOLATED at ' + json.dumps(meta))
            rows.append(row)

        require(len(plan['references']) == 24, 'reference count')
        for index, ref in enumerate(plan['references']):
            d = gate / f'ref_{index:02d}'
            v = load(d / 'validation.json')
            require(v['valid'] and v['reference'] == ref
                    and v['provenance'] == plan['provenance'], 'validation mismatch')
            for name, h in v['artifacts'].items():
                verify(d / name, h)
            verify(study / ref['path'], ref['sha256'])
            branches = load(d / 'branches.json')
            parts = Path(ref['path']).parts
            seed = int(Path(ref['path']).stem.split('seed')[1])
            for r in ROUNDS:
                cap = load(d / f'round_{r:02d}_state.json')
                record(d / f'round_{r:02d}_updates.npy')
                matrix = np.load(d / f'round_{r:02d}_updates.npy', allow_pickle=False)
                for mode, fn in [('original', mod.fed_mdbscan_g_filter),
                                 ('density_only', forced)]:
                    choices = [b for b in branches
                               if b['round'] == r and b['gate'] == mode and b['cutoff']]
                    require(len(choices) == 1, 'branch uniqueness')
                    b = choices[0]
                    require(cap['participants'] == b['participant_ids'], 'participant order')
                    evaluate(mod, fn, matrix, cap['params'], cap['participants'],
                             b['actual_malicious_ids'],
                             dict(scope='gate_v2', reference=index, dataset=parts[2],
                                  seed=seed, condition=parts[1], scenario=parts[3],
                                  round=r, gate=mode))
            print(f'reference {index + 1}/24 done; {len(rows)} checkpoints', flush=True)

        # historical A/B/C arms (attack-free, all 90 participants honest)
        forward, abc = root / FORWARD, root / ABC
        manifest = load(forward / 'manifest.json')
        for name, h in manifest['files'].items():
            verify(forward / name, h)
        oldmod = module_at(forward / 'source/new_work/simulation/mdbscan.py', 'abc_frozen')
        ck = load(forward / 'reference/mnist_2024/checkpoints/round_009.json')
        cfg = load(forward / 'configs/mnist_2024_branch.json')
        params = {**cfg['method_params']['fed_mdbscan_g'],
                  'attack_history': ck['defense_state']['detected_attack_history'],
                  'clean_round_streak': ck['defense_state']['clean_round_streak']}
        for arm in 'ABC':
            payload = load(abc / f'{arm}.json')
            mp = abc / f'{arm}_updates.npy'
            record(mp)
            matrix = np.load(mp, allow_pickle=False)
            require(hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest()
                    == payload['input_sha256'], 'ABC matrix content')
            evaluate(oldmod, oldmod.fed_mdbscan_g_filter, matrix, params, payload['ids'],
                     payload['record']['actual_malicious_ids'],
                     dict(scope='historical_abc', reference=arm, dataset='mnist', seed=2024,
                          condition='clean', scenario='ABC', round=9, gate='original'))

        require(len(rows) == 24 * len(ROUNDS) * 2 + 3, f'coverage: got {len(rows)}')
        for name, h in inputs.items():
            require(sha(root / name) == h, 'input changed during run ' + name)

        with (out / 'gamma.csv').open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

        def summarize(sel, label):
            g = [r['gamma'] for r in rows if sel(r)]
            if not g:
                return None
            return dict(label=label, n=len(g),
                        min=min(g), median=st.median(g), max=max(g),
                        frac_vacuous=sum(1 for r in rows if sel(r) and r['vacuous']) / len(g),
                        any_cluster_rejected=sum(1 for r in rows if sel(r)
                                                 and r['any_cluster_rejected']))

        summary = [s for s in [
            summarize(lambda r: True, 'all checkpoints'),
            summarize(lambda r: r['scope'] == 'gate_v2', 'gate_v2 (72 matrices x 2 gates)'),
            summarize(lambda r: r['malicious_count'] > 0, 'attacked checkpoints'),
            summarize(lambda r: r['malicious_count'] == 0, 'attack-free checkpoints'),
            summarize(lambda r: r['gate'] == 'original', 'deployed gate'),
            summarize(lambda r: r['gate'] == 'density_only', 'density-only gate'),
            summarize(lambda r: r['scope'] == 'historical_abc', 'historical A/B/C'),
        ] if s]

        (out / 'summary.json').write_text(json.dumps(dict(
            summary=summary,
            proposition_3_hypothesis='gamma <= tau => consensus test cannot reject any subset of B0',
            note=('Fixed-geometry measurement on recorded matrices. No training, no '
                  'accuracy or attack-success measurement. A checkpoint with '
                  'vacuous=true had an inert clustering stage by construction.'),
            inputs_sha256=inputs,
            script_sha256=sha(__file__),
            numpy_version=np.__version__,
        ), indent=2) + '\n')

        print('\n=== Gamma summary ===')
        for s in summary:
            print(f"{s['label']:<34s} n={s['n']:<4d} median={s['median']:.3f} "
                  f"max={s['max']:.3f} vacuous={100 * s['frac_vacuous']:.1f}% "
                  f"cluster-rejections={s['any_cluster_rejected']}")
        print('\nCOMPLETE. Write the "attacked checkpoints" row into the manuscript.')

    except BaseException:
        (out / 'failure.json').write_text(json.dumps(
            dict(completed_rows=len(rows), traceback=traceback.format_exc()), indent=2) + '\n')
        raise


if __name__ == '__main__':
    main()
