"""Offline feasibility probe for scalar temporal signatures. Implements PROTOCOL.md.

Reads the completed cutoff development study and asks whether any per-client
statistic computed across rounds separates attackers where single-round geometry
does not. Trains nothing and writes only into this directory.

The attacked arm and its attack-disabled placebo share partition, initial model,
participation schedule and the same eighteen latent attacker identities, so a
statistic that separates those clients in both arms is detecting the client
rather than the attack.

    .venv/bin/python analysis/temporal_signature_20260919/run_probe.py
"""

import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path('/home/gokcen/Fed_MDBSCAN_TIFS')
HERE = Path(__file__).resolve().parent
STUDY = ROOT / 'new_work/results/cutoff_development/study_20260914_v1/runs'

DATASETS = ['mnist', 'fashion_mnist']
SCENARIOS = ['cut_minmax', 'cut_gaussian', 'cut_backdoor']
SEEDS = [42, 137, 2024]
# fedavg never rejects, so its trajectories are not shaped by the defense's own
# filtering feedback; fed_mdbscan_g is kept as a transfer check.
METHODS = ['fedavg', 'fed_mdbscan_g']

# Declared before any result was computed. Only lag1 carries a one-sided
# prediction; the rest are reported two-sided and labelled exploratory.
ORIENTED = {'lag1': -1.0}
EXPLORATORY = ('rel_cv', 'trend')
CONTROL = 'rel_mean'
STATISTICS = (CONTROL, 'lag1', 'rel_cv', 'trend')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spearman(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None

    def rank(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        index = 0
        while index < len(order):
            stop = index
            while stop + 1 < len(order) and values[order[stop + 1]] == values[order[index]]:
                stop += 1
            shared = (index + stop) / 2.0 + 1.0
            for position in range(index, stop + 1):
                out[order[position]] = shared
            index = stop + 1
        return out

    rx, ry = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    if len(set(rx)) < 2 or len(set(ry)) < 2:
        return None
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else None


def auc(positive, negative):
    if not positive or not negative:
        return None
    ordered = sorted([(v, 1) for v in positive] + [(v, 0) for v in negative])
    ranks, index = {}, 0
    while index < len(ordered):
        stop = index
        while stop + 1 < len(ordered) and ordered[stop + 1][0] == ordered[index][0]:
            stop += 1
        shared = (index + stop) / 2.0 + 1.0
        for position in range(index, stop + 1):
            ranks[position] = shared
        index = stop + 1
    n_pos, n_neg = len(positive), len(negative)
    rank_sum = sum(ranks[i] for i, (_, label) in enumerate(ordered) if label == 1)
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def client_series(payload):
    """Per client: relative norm per participating round, plus confounds."""
    records = payload['records']
    metadata = payload['run_metadata']['client_metadata']
    series, steps, rounds = {}, {}, {}
    for record in records:
        ids = [str(c) for c in record['server_input_ids']]
        norms = [record['update_norms'].get(i) for i in ids]
        present = [n for n in norms if n is not None]
        if not present:
            continue
        median = statistics.median(present)
        if median <= 0:
            continue
        for cid, norm in zip(ids, norms):
            if norm is None:
                continue
            series.setdefault(cid, []).append(norm / median)
            rounds.setdefault(cid, []).append(record['round'])
            steps.setdefault(cid, []).append(record['optimizer_steps'][cid])

    out = {}
    for cid, values in series.items():
        if len(values) < 5:
            continue
        mean = statistics.fmean(values)
        sd = statistics.stdev(values) if len(values) > 1 else 0.0
        out[cid] = dict(
            rel_mean=mean,
            rel_cv=(sd / mean) if mean else None,
            lag1=spearman(values[:-1], values[1:]),
            trend=spearman(values, rounds[cid]),
            sample_count=metadata[cid]['sample_count'],
            mean_steps=statistics.fmean(steps[cid]),
            observed_rounds=len(values))
    return out


def evaluate(payload, marked_ids):
    """AUC of each statistic for the marked clients against the rest."""
    stats = client_series(payload)
    marked = {str(c) for c in marked_ids}
    item = dict(clients=len(stats), marked=sum(1 for c in stats if c in marked))
    for name in STATISTICS:
        positive = [s[name] for c, s in stats.items() if c in marked and s[name] is not None]
        negative = [s[name] for c, s in stats.items() if c not in marked and s[name] is not None]
        raw = auc(positive, negative)
        item[f'auc_{name}'] = raw
        if raw is not None and name in ORIENTED:
            # Oriented statistic: score with the declared sign, no post-hoc flip.
            item[f'oriented_{name}'] = auc([-v for v in positive], [-v for v in negative])
        if raw is not None and name in EXPLORATORY:
            item[f'twosided_{name}'] = abs(raw - 0.5)
        values = [(s[name], s['sample_count'], s['mean_steps'])
                  for s in stats.values() if s[name] is not None]
        if values:
            item[f'rho_{name}_samples'] = spearman([v[0] for v in values], [v[1] for v in values])
            item[f'rho_{name}_steps'] = spearman([v[0] for v in values], [v[2] for v in values])
    return item


def main():
    rows, sources = [], {}
    for method in METHODS:
        for dataset in DATASETS:
            for scenario in SCENARIOS:
                for seed in SEEDS:
                    attacked = (STUDY / f'cutoff_attacked/{dataset}/scenario_{scenario}'
                                / f'runs/{method}_seed{seed}.json')
                    placebo = (STUDY / f'cutoff_clean/{dataset}/scenario_{scenario}'
                               / f'runs/{method}_seed{seed}.json')
                    if not attacked.exists() or not placebo.exists():
                        continue
                    a_payload = json.loads(attacked.read_text())
                    p_payload = json.loads(placebo.read_text())
                    sources[str(attacked.relative_to(ROOT))] = sha256(attacked)
                    sources[str(placebo.relative_to(ROOT))] = sha256(placebo)

                    a_meta, p_meta = a_payload['run_metadata'], p_payload['run_metadata']
                    matched = all(a_meta[k] == p_meta[k] for k in
                                  ('partition_sha256', 'initial_model_sha256', 'schedule_sha256'))
                    attackers = a_payload['records'][0]['actual_malicious_ids']
                    latent = p_payload['records'][0]['latent_malicious_ids']
                    if sorted(attackers) != sorted(latent):
                        raise SystemExit(f'identity mismatch for {method}/{dataset}/{scenario}/{seed}')

                    base = dict(method=method, dataset=dataset,
                                scenario=scenario.replace('cut_', ''), seed=seed,
                                pair_matched=matched, attackers=len(attackers))
                    rows.append(dict(base, arm='attacked', **evaluate(a_payload, attackers)))
                    rows.append(dict(base, arm='placebo', **evaluate(p_payload, latent)))

    if not rows:
        raise SystemExit('no runs found')

    fields = list(rows[0])
    with (HERE / 'per_run.csv').open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in rows:
            handle.write(','.join('' if row.get(f) is None else str(row.get(f, ''))
                                  for f in fields) + '\n')

    summary = []
    for method in METHODS:
        for scenario in ('minmax', 'gaussian', 'backdoor'):
            for arm in ('attacked', 'placebo'):
                cell = [r for r in rows if r['method'] == method
                        and r['scenario'] == scenario and r['arm'] == arm]
                if not cell:
                    continue
                item = dict(method=method, scenario=scenario, arm=arm, runs=len(cell))
                for name in STATISTICS:
                    key = f'oriented_{name}' if name in ORIENTED else f'auc_{name}'
                    values = [r[key] for r in cell if r.get(key) is not None]
                    item[f'{name}_auc_median'] = (
                        round(statistics.median(values), 4) if values else None)
                    item[f'{name}_auc_min'] = round(min(values), 4) if values else None
                    item[f'{name}_auc_max'] = round(max(values), 4) if values else None
                summary.append(item)

    fields = list(summary[0])
    with (HERE / 'summary_by_condition.csv').open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in summary:
            handle.write(','.join('' if row[f] is None else str(row[f]) for f in fields) + '\n')

    confounds = {}
    for name in STATISTICS:
        for target in ('samples', 'steps'):
            values = [r[f'rho_{name}_{target}'] for r in rows
                      if r.get(f'rho_{name}_{target}') is not None]
            confounds[f'{name}_vs_{target}'] = (
                round(statistics.median(values), 4) if values else None)

    report = dict(runs=len(rows) // 2,
                  all_pairs_matched=all(r['pair_matched'] for r in rows),
                  oriented=ORIENTED, exploratory=list(EXPLORATORY), control=CONTROL,
                  confound_rho_median=confounds, by_condition=summary)
    (HERE / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'provenance.json').write_text(json.dumps(dict(
        read_only=True, script_sha256=sha256(__file__),
        protocol_sha256=sha256(HERE / 'PROTOCOL.md'), inputs=sources), indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'by_condition'}, indent=2))


if __name__ == '__main__':
    main()
