"""Read-only evaluation of the root-signal checkpoint probe.

Consumes ``root_scores.json`` from every completed reference of
``new_work/results/mechanism_root_signal/probe_20260919_v1`` and reports what
``PROTOCOL.md`` fixed in advance: per-checkpoint delta norms, both root scores,
undefined counts, the floor/above-floor split, attacker and honest
distributions, and descriptive AUC on the attacked arm.

No threshold is chosen, no decision is changed, no accuracy or ASR is computed.
Ground-truth attacker identity is read only here, after scoring.

Two negative controls are included because this project has repeatedly found
that a geometric signal turns out to track update magnitude or local data
volume rather than adversarial behaviour:

* ``delta_norm`` is scored as a rival ranking. A root score that does not
  separate better than the plain update norm adds nothing.
* the rank correlation of each root score with ``delta_norm`` and with
  ``sample_count`` is reported, so a score that is a norm detector or a
  data-volume detector in disguise is visible.

    .venv/bin/python analysis/root_signal_20260919/evaluate_scores.py [probe_dir]

Descriptive only: three seeds, correlated checkpoints, no significance claim.
Partial runs are accepted; the reference count is reported.
"""

import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path('/home/gokcen/Fed_MDBSCAN_TIFS')
HERE = Path(__file__).resolve().parent
DEFAULT_PROBE = ROOT / 'new_work/results/mechanism_root_signal/probe_20260919_v1'

# Larger means more suspicious for every score, so AUC is directly comparable.
SCORES = ('negative_root_cosine', 'root_loss_delta', 'delta_norm')
FLOOR = 20


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def auc(positive, negative):
    """Mann-Whitney AUC with ties counted as half; None when a class is empty."""
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
            ranks.setdefault(position, shared)
        index = stop + 1
    positive_rank_sum = sum(ranks[i] for i, (_, label) in enumerate(ordered) if label == 1)
    n_pos, n_neg = len(positive), len(negative)
    return (positive_rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def spearman(xs, ys):
    """Rank correlation; None when either variable is constant."""
    pairs = [(x, y) for x, y in zip(xs, ys)
             if x is not None and y is not None
             and not (isinstance(x, float) and math.isnan(x))]
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


def describe(values):
    values = [v for v in values if v is not None]
    if not values:
        return dict(n=0, median=None, q1=None, q3=None)
    ordered = sorted(values)
    return dict(
        n=len(ordered),
        median=statistics.median(ordered),
        q1=ordered[max(0, len(ordered) // 4 - 1)],
        q3=ordered[min(len(ordered) - 1, (3 * len(ordered)) // 4)])


def reference_identity(path):
    """dataset / attack / mode / seed taken from the frozen reference path."""
    parts = Path(path).parts
    mode = 'attacked' if 'cutoff_attacked' in parts[1] else 'clean'
    dataset = parts[2]
    attack = parts[3].replace('scenario_cut_', '')
    seed = int(Path(parts[-1]).stem.split('seed')[-1])
    return dict(dataset=dataset, attack=attack, mode=mode, seed=seed)


def main():
    probe = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PROBE
    status = json.loads((probe / 'status.json').read_text())

    rows, sources, references = [], {}, []
    for ref_dir in sorted(probe.glob('ref_*')):
        scores_path = ref_dir / 'root_scores.json'
        validation_path = ref_dir / 'validation.json'
        if not scores_path.exists() or not validation_path.exists():
            continue
        validation = json.loads(validation_path.read_text())
        if not validation.get('valid'):
            continue
        payload = json.loads(scores_path.read_text())
        sources[str(scores_path.relative_to(probe))] = sha256(scores_path)
        identity = reference_identity(payload['reference']['path'])
        references.append(dict(ref=ref_dir.name, **identity,
                               matched_rounds=validation['matched_rounds'],
                               client_scores=validation['client_scores']))
        for checkpoint in payload['checkpoints']:
            for row in checkpoint['rows']:
                rows.append(dict(
                    ref=ref_dir.name, **identity, round=checkpoint['round'],
                    base_loss=checkpoint['base_loss'],
                    root_gradient_norm=checkpoint['root_gradient_norm'],
                    client_id=row['client_id'],
                    attacker=bool(row['actual_attacker']),
                    sample_count=row['sample_count'],
                    size_quartile=row['size_quartile'],
                    dominant_label=row['dominant_label'],
                    at_floor=row['sample_count'] <= FLOOR,
                    **{name: row.get(name) for name in SCORES}))

    if not rows:
        raise SystemExit('no completed reference with valid scores yet')

    # ---- per checkpoint: separation on the attacked arm, and controls -------
    per_checkpoint = []
    keys = sorted({(r['dataset'], r['attack'], r['mode'], r['seed'], r['round']) for r in rows})
    for dataset, attack, mode, seed, rnd in keys:
        cell = [r for r in rows
                if (r['dataset'], r['attack'], r['mode'], r['seed'], r['round'])
                == (dataset, attack, mode, seed, rnd)]
        attackers = [r for r in cell if r['attacker']]
        honest = [r for r in cell if not r['attacker']]
        item = dict(dataset=dataset, attack=attack, mode=mode, seed=seed, round=rnd,
                    clients=len(cell), attackers=len(attackers),
                    undefined_cosine=sum(1 for r in cell if r['negative_root_cosine'] is None),
                    zero_norm=sum(1 for r in cell if (r['delta_norm'] or 0) == 0),
                    base_loss=cell[0]['base_loss'])
        for name in SCORES:
            item[f'auc_{name}'] = auc([r[name] for r in attackers if r[name] is not None],
                                      [r[name] for r in honest if r[name] is not None])
            item[f'rho_{name}_vs_norm'] = spearman([r[name] for r in cell],
                                                   [r['delta_norm'] for r in cell])
            item[f'rho_{name}_vs_samples'] = spearman([r[name] for r in cell],
                                                      [r['sample_count'] for r in cell])
            floor_values = [r[name] for r in cell if r['at_floor']]
            above_values = [r[name] for r in cell if not r['at_floor']]
            item[f'{name}_floor_median'] = describe(floor_values)['median']
            item[f'{name}_above_median'] = describe(above_values)['median']
        per_checkpoint.append(item)

    # ---- pooled by condition and round, keeping datasets separate ----------
    by_condition = []
    for dataset, attack, mode, rnd in sorted({
            (r['dataset'], r['attack'], r['mode'], r['round']) for r in rows}):
        cell = [c for c in per_checkpoint
                if (c['dataset'], c['attack'], c['mode'], c['round'])
                == (dataset, attack, mode, rnd)]
        raw = [r for r in rows
               if (r['dataset'], r['attack'], r['mode'], r['round'])
               == (dataset, attack, mode, rnd)]
        item = dict(dataset=dataset, attack=attack, mode=mode, round=rnd,
                    seeds=len(cell), clients=len(raw),
                    attackers=sum(c['attackers'] for c in cell))
        for name in SCORES:
            values = [c[f'auc_{name}'] for c in cell if c[f'auc_{name}'] is not None]
            item[f'auc_{name}_median'] = statistics.median(values) if values else None
            item[f'auc_{name}_min'] = min(values) if values else None
            item[f'auc_{name}_max'] = max(values) if values else None
            attacker_stats = describe([r[name] for r in raw if r['attacker']])
            honest_stats = describe([r[name] for r in raw if not r['attacker']])
            item[f'{name}_attacker_median'] = attacker_stats['median']
            item[f'{name}_honest_median'] = honest_stats['median']
        by_condition.append(item)

    def write_csv(path, records):
        if not records:
            return
        fields = list(records[0])
        with Path(path).open('w') as handle:
            handle.write(','.join(fields) + '\n')
            for record in records:
                handle.write(','.join(
                    '' if record[f] is None else str(record[f]) for f in fields) + '\n')

    write_csv(HERE / 'eval_per_checkpoint.csv', per_checkpoint)
    write_csv(HERE / 'eval_by_condition.csv', by_condition)
    write_csv(HERE / 'eval_references.csv', references)

    summary = dict(
        probe=str(probe.relative_to(ROOT)),
        probe_state=status['state'],
        references_completed=len(references),
        references_expected=status.get('expected_references'),
        checkpoints=len(per_checkpoint),
        client_checkpoint_rows=len(rows),
        by_condition=by_condition)
    (HERE / 'eval_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (HERE / 'eval_provenance.json').write_text(json.dumps(dict(
        read_only=True, probe=str(probe.relative_to(ROOT)),
        script_sha256=sha256(__file__), inputs=sources), indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'by_condition'}, indent=2))


if __name__ == '__main__':
    main()
