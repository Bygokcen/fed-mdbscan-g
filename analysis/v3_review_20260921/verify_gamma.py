"""Independent reductions of archived geometry; does not run the defense."""
import argparse
import csv
import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--gamma', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = a.root.resolve()
    gate = root / 'new_work/results/mechanism_gate_replay/replay_20260915_v2'
    src = root / 'new_work/results/cutoff_development/study_20260914_v1/source/new_work/simulation/mdbscan.py'
    spec = importlib.util.spec_from_file_location('gamma_check_frozen', src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = list(csv.DictReader((a.gamma / 'gamma.csv').open()))
    summary = json.loads((a.gamma/'summary.json').read_text())
    assert len(rows) == 147
    for path, digest in summary['inputs_sha256'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest() == digest, path
    unique = [r for r in rows if r['scope']=='gate_v2' and r['gate']=='original']
    assert len(unique) == 72
    verified, mixed, changed = [], [], []
    for row in unique:
        directory = gate / ('ref_%02d' % int(row['reference']))
        branches = json.loads((directory/'branches.json').read_text())
        original = next(b for b in branches if b['round']==int(row['round'])
                        and b['gate']=='original' and b['cutoff'])
        geom = original['geometry']
        b0 = sorted(geom['l0_benign'])
        x = np.load(directory / ('round_%02d_updates.npy' % int(row['round'])), allow_pickle=False)
        native_centre = mod._weiszfeld_geometric_median(x[b0])
        native_radii = np.linalg.norm(x[b0]-native_centre, axis=1)
        native_gamma = float(max(native_radii)/max(float(np.median(native_radii)),1e-10))
        # The supplied gamma script promotes the centre to float64; reproduce
        # that convention explicitly, also check native-precision classification.
        centre = np.asarray(native_centre, dtype=float)
        distances = np.sqrt(np.sum((x[b0]-centre)**2, axis=1))
        med = statistics.median(distances.tolist())
        gamma = float(max(distances)/max(med,1e-10))
        assert abs(gamma-float(row['gamma'])) <= 1e-12, row
        assert (gamma<=2) == (native_gamma<=2), row
        changed.append(abs(gamma-native_gamma))
        assert len(b0) == int(row['b0_size'])
        forced = next(b for b in branches if b['round']==int(row['round'])
                      and b['gate']=='density_only' and b['cutoff'])
        other = next(r for r in rows if r['scope']=='gate_v2'
                     and r['reference']==row['reference'] and r['round']==row['round']
                     and r['gate']=='density_only')
        assert b0 == sorted(forced['geometry']['l0_benign'])
        assert row['gamma'] == other['gamma']
        for branch in (original, forced):
            groups = branch['geometry'].get('natural_clusters', [])
            outside = [s for s in groups if not set(s)<=set(b0)]
            if outside:
                mixed.append(dict(reference=row['reference'], round=row['round'], gate=branch['gate'],
                                  groups_not_contained_in_b0=len(outside), gamma=gamma))
        verified.append(dict(reference=row['reference'], dataset=row['dataset'],
                             scenario=row['scenario'], seed=row['seed'], round=row['round'],
                             attacked=int(row['malicious_count'])>0, gamma=gamma,
                             b0_equals_all=len(b0)==len(x)))
    attacked = [r for r in verified if r['attacked']]
    assert len(attacked)==36 and all(r['b0_equals_all'] for r in attacked)
    result = dict(verified_unique_matrices=len(verified), gate_rows=144,
                  attacked_unique_matrices=len(attacked),
                  max_native_vs_promoted_gamma_difference=max(changed),
                  precision_changes_tau_classification=0,
                  attacked_satisfying=sum(r['gamma']<=2 for r in attacked),
                  attacked_gamma_min=min(r['gamma'] for r in attacked),
                  attacked_gamma_median=statistics.median(r['gamma'] for r in attacked),
                  attacked_gamma_max=max(r['gamma'] for r in attacked),
                  attacked_exceptions=[r for r in attacked if r['gamma']>2],
                  archived_branches_with_clusters_outside_b0=mixed,
                  note='Independent radius reduction from recorded B0; same frozen geometric-median routine. No independent training replication. Historical ABC not recomputed here.')
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='archived_branches_with_clusters_outside_b0'},indent=2))


if __name__=='__main__':
    main()
