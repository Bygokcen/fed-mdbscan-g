#!/usr/bin/env python3
"""Summarise the review experiments exactly as PROTOCOL.md specifies.

Reads OUT/units/*/ (see review_runner.py) and the canonical archive, and writes
next to this script:
    e1_conditions.csv      mechanism under the canonical protocol, per scenario and dataset
    e2a_fidelity.csv       FLAME clustering, local selector versus reference hdbscan
    e23_accuracy.csv       final accuracy per dataset and seed for the controls
    review_summary.json    pooled values used in the manuscript, with provenance
"""
import csv
import hashlib
import json
import pathlib
import statistics as st
from collections import defaultdict

ROOT = pathlib.Path('/home/gokcen/Fed_MDBSCAN_TIFS')
CANON = ROOT / 'new_work/results/validated/audit-v2/full_20260910'
OUT = ROOT / 'new_work/results/review_20260926'
HERE = pathlib.Path(__file__).resolve().parent
SEEDS = (42, 137, 2024)
SCENARIO = {'7.1': 'Min-Max, alpha=0.1', '7.2': 'Min-Sum, alpha=0.01', '8.1': 'patch, alpha=0.1',
            '8.2': 'patch, alpha=0.01', '6.2': 'clean, alpha=0.01'}


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(pathlib.Path(path).read_text())


def require(ok, label):
    if not ok:
        raise RuntimeError(label)


def canonical_final(dataset, scenario, method, seed):
    run = load(CANON / 'runs/main' / dataset / f'scenario_{scenario}' / 'runs' / f'{method}_seed{seed}.json')
    return run['records'][-1]['accuracy']


def ber(records):
    fp = sum(r['fp'] for r in records)
    tn = sum(r['tn'] for r in records)
    return fp / (fp + tn)


def main():
    plan = load(OUT / 'plan.json')
    units = {u['id']: u for u in plan['units']}
    done, failed = {}, []
    for uid in units:
        d = OUT / 'units' / uid
        if (d / 'done.json').exists():
            done[uid] = load(d / 'done.json')
        else:
            failed.append(uid)
    provenance = dict(plan_sha256=sha(OUT / 'plan.json'), runner_sha256=plan['runner_sha256'],
                      protocol_sha256=plan['protocol_sha256'], script_sha256=sha(__file__),
                      units_done=len(done), units_missing_or_failed=sorted(failed))

    # ---------------- E1
    e1_rows, e1_pool = [], defaultdict(lambda: defaultdict(float))
    for sc in SCENARIO:
        for ds in ('mnist', 'fashion_mnist'):
            acc = defaultdict(float)
            gammas = []
            for seed in SEEDS:
                uid = f'E1_{ds}_{sc}_{seed}'
                if uid not in done:
                    continue
                d = OUT / 'units' / uid
                acc['runs'] += 1
                acc['exact_runs'] += int(done[uid]['exact_reproduction'])
                matrices = {m['round']: m for m in load(d / 'matrices.json')}
                branches = load(d / 'branches.json')
                for r, m in matrices.items():
                    by = {(b['gate'], b['cutoff']): b for b in branches if b['round'] == r}
                    deployed, forced = by[('original', True)], by[('density_only', True)]
                    acc['matrices'] += 1
                    acc['attacked'] += int(m['malicious_count'] > 0)
                    acc['b0_full'] += int(m['b0_size'] == deployed['n'])
                    acc['gamma_le_tau'] += int(m['gamma_le_tau'])
                    gammas.append(m['gamma'])
                    acc['deployed_gate_ran'] += int(deployed['partition_executed'])
                    acc['forced_gate_ran'] += int(forced['partition_executed'])
                    subset = forced['partition_executed'] and forced['groups_outside_b0'] == 0
                    # Exploratory breakdown (not pre-specified in PROTOCOL.md).
                    acc['x_forced_matrices_with_groups'] += int(forced['n_groups'] > 0)
                    acc['x_forced_matrices_groups_nonempty_in_b0'] += int(forced['n_groups'] > 0 and forced['groups_outside_b0'] == 0)
                    acc['x_forced_matrices_with_group_rejection'] += int(forced['rejected_group_members'] > 0)
                    acc['x_forced_rejection_without_b0_effect'] += int(forced['rejected_group_members'] > 0 and forced['removed_from_b0'] == 0)
                    acc['x_b0_size_total'] += m['b0_size']
                    acc['groups_in_b0'] += int(subset)
                    acc['sufficient_condition'] += int(subset and m['gamma_le_tau'])
                    for tag, b in (('deployed', deployed), ('forced', forced)):
                        acc[f'{tag}_matrices_with_removal'] += int(b['removed_from_b0'] > 0)
                        acc[f'{tag}_removed_honest'] += b['removed_from_b0_honest']
                        acc[f'{tag}_removed_attackers'] += b['removed_from_b0_attackers']
                    acc['attackers_total'] += deployed['malicious_count']
                    acc['attackers_outside_b0'] += deployed['tp'] - deployed['removed_from_b0_attackers']
            row = dict(scenario=sc, condition=SCENARIO[sc], dataset=ds,
                       gamma_median=round(st.median(gammas), 6) if gammas else None,
                       gamma_max=round(max(gammas), 6) if gammas else None,
                       **{k: int(v) for k, v in acc.items()})
            e1_rows.append(row)
            for k, v in acc.items():
                e1_pool[sc][k] += v
            e1_pool[sc].setdefault('gammas', [])
            e1_pool[sc]['gammas'] += gammas
    with open(HERE / 'e1_conditions.csv', 'w', newline='') as fh:
        fields = sorted({k for r in e1_rows for k in r}, key=lambda k: (k not in ('scenario', 'condition', 'dataset'), k))
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(e1_rows)
    e1_summary = []
    for sc, v in e1_pool.items():
        g = v.pop('gammas')
        e1_summary.append(dict(scenario=sc, condition=SCENARIO[sc],
                               gamma_median=round(st.median(g), 6) if g else None,
                               gamma_max=round(max(g), 6) if g else None,
                               **{k: int(x) for k, x in v.items()}))

    # ---------------- E2a
    e2a_rows = []
    for ds, sc in (('mnist', '1.1'), ('mnist', '6.2'), ('har', '6.2')):
        acc = defaultdict(int)
        diffs = []
        for seed in SEEDS:
            uid = f'E2a_{ds}_{sc}_{seed}'
            if uid not in done:
                continue
            rows = load(OUT / 'units' / uid / 'fidelity_rounds.json')
            acc['runs'] += 1
            acc['exact_runs'] += int(done[uid]['exact_reproduction'])
            acc['clustered_rounds'] += len(rows)
            acc['equal_rounds'] += sum(r['equal'] for r in rows)
            acc['reference_larger'] += sum(r['reference_size'] > r['local_size'] for r in rows)
            acc['reference_smaller'] += sum(r['reference_size'] < r['local_size'] for r in rows)
            diffs += [r['symmetric_difference'] for r in rows]
        e2a_rows.append(dict(dataset=ds, scenario=sc, max_symmetric_difference=max(diffs) if diffs else None, **acc))
    with open(HERE / 'e2a_fidelity.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(e2a_rows[0]))
        w.writeheader()
        w.writerows(e2a_rows)

    # ---------------- E2b and E3
    acc_rows = []
    for ds in ('mnist', 'fashion_mnist', 'har'):
        for seed in SEEDS:
            row = dict(dataset=ds, seed=seed,
                       fedavg=canonical_final(ds, '6.2', 'fedavg', seed),
                       flame=canonical_final(ds, '6.2', 'flame_hdbscan', seed),
                       multikrum=canonical_final(ds, '6.2', 'krum_bound30', seed))
            for tag, uid in (('flame_nonoise', f'E2b_{ds}_6.2_{seed}'), ('flame_random', f'E3f_{ds}_6.2_{seed}'),
                             ('multikrum_random', f'E3k_{ds}_6.2_{seed}')):
                if uid in done:
                    rec = load(OUT / 'units' / uid / 'records.json')
                    row[tag] = rec['records'][-1]['accuracy']
                    row[tag + '_ber'] = ber(rec['records'])
                    if tag != 'flame_nonoise':
                        audit = rec['selection_audit']
                        row[tag + '_mean_overlap'] = st.mean(a['overlap_with_rule'] / a['size'] for a in audit)
                else:
                    row[tag] = None
            acc_rows.append(row)
    with open(HERE / 'e23_accuracy.csv', 'w', newline='') as fh:
        fields = sorted({k for r in acc_rows for k in r}, key=lambda k: (k not in ('dataset', 'seed'), k))
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(acc_rows)

    def mean_of(ds, key):
        vals = [r[key] for r in acc_rows if r['dataset'] == ds and r.get(key) is not None]
        return round(100 * st.mean(vals), 2) if len(vals) == 3 else None

    def paired(ds, a, b):
        vals = [100 * (r[a] - r[b]) for r in acc_rows if r['dataset'] == ds and r.get(a) is not None and r.get(b) is not None]
        return dict(mean=round(st.mean(vals), 2), min=round(min(vals), 2), max=round(max(vals), 2)) if len(vals) == 3 else None

    e23_summary = []
    for ds in ('mnist', 'fashion_mnist', 'har'):
        e23_summary.append(dict(
            dataset=ds, fedavg=mean_of(ds, 'fedavg'), flame=mean_of(ds, 'flame'),
            flame_nonoise=mean_of(ds, 'flame_nonoise'), flame_random=mean_of(ds, 'flame_random'),
            multikrum=mean_of(ds, 'multikrum'), multikrum_random=mean_of(ds, 'multikrum_random'),
            noise_effect=paired(ds, 'flame_nonoise', 'flame'),
            flame_minus_random=paired(ds, 'flame', 'flame_random'),
            multikrum_minus_random=paired(ds, 'multikrum', 'multikrum_random'),
            fedavg_minus_flame_random=paired(ds, 'fedavg', 'flame_random'),
            fedavg_minus_multikrum_random=paired(ds, 'fedavg', 'multikrum_random')))

    summary = dict(provenance=provenance, e1=e1_summary, e2a=e2a_rows, e23=e23_summary)
    (HERE / 'review_summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
