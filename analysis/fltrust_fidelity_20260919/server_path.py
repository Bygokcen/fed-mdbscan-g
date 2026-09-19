"""FLTrust through the real server, plus the edge cases the rule check missed.

`compare.py` compares formulas: it calls the local filter but restates the
server-side aggregation. This script instead drives `Server.aggregate` itself, so
the path that produced the canonical results is the one under test, and then
exercises the boundaries that the formula comparison skipped:

* every trust score zero,
* a zero root update,
* client norms and trust scores at the guard thresholds.

Finally it counts whether those fallback paths ever fired in the canonical
FLTrust runs, which is what decides whether any recorded result is affected.

    .venv/bin/python analysis/fltrust_fidelity_20260919/server_path.py

Read-only over the archives; writes only into this directory.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path('/home/gokcen/Fed_MDBSCAN_TIFS')
HERE = Path(__file__).resolve().parent
GATE = ROOT / 'new_work/results/mechanism_gate_replay/replay_20260915_v2'
CANONICAL = ROOT / 'new_work/results/validated/audit-v2/full_20260910/runs'
sys.path.insert(0, str(ROOT / 'new_work'))

from compare import published_fltrust, root_constructions  # noqa: E402


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def server_aggregate(updates, root_update, method):
    """Run the real Server.aggregate with a pinned root update.

    Only `_train_root_gradient` is replaced, so the filter, the fallback policy
    and the aggregation branch are the ones the canonical runs used.
    """
    import torch
    from simulation.server import Server

    matrix = np.asarray(updates, dtype=np.float32)
    dimension = matrix.shape[1]
    model = torch.nn.Linear(dimension, 1, bias=False)
    with torch.no_grad():
        model.weight.zero_()

    server = Server(model=model, test_loader=[], aggregation_method=method,
                    method_params={'root_lr': 0.01, 'root_epochs': 1})
    server.root_model = model            # presence is enough; the call is replaced
    server.root_loader = [()]
    server._train_root_gradient = lambda **kwargs: np.asarray(root_update, dtype=np.float64)

    before = server.get_global_weights()
    result = server.aggregate([row.copy() for row in matrix],
                              participating_ids=list(range(len(matrix))), round_id=0)
    after = server.get_global_weights()
    return dict(applied_update=after - before,
                accepted=len(result['decision']['accepted_ids']),
                rejected=len(result['decision']['rejected_ids']),
                operator=result['decision']['aggregation_operator'],
                fallback_reason=result['filter_info'].get('fallback_reason', 'none'),
                degraded=bool(result['filter_info'].get('degraded', False)))


def agreement(applied, reference_aggregate):
    left = np.asarray(applied, dtype=np.float64)
    right = np.asarray(reference_aggregate, dtype=np.float64)
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return dict(
        relative_gap=float(np.linalg.norm(left - right) / (np.linalg.norm(right) or 1.0)),
        cosine=float(left @ right / denominator) if denominator else None,
        applied_norm=float(np.linalg.norm(left)),
        reference_norm=float(np.linalg.norm(right)))


# ----------------------------------------------------------------------
def real_path_cases(sources):
    """The same inputs as the rule check, now through Server.aggregate."""
    rows = []
    rng = np.random.default_rng(20260919)
    matrices = 0
    for ref_dir in sorted(GATE.glob('ref_*')):
        for rnd in (0, 9, 29):
            path = ref_dir / f'round_{rnd:02d}_updates.npy'
            if not path.exists():
                continue
            matrix = np.load(path)
            sources[str(path.relative_to(ROOT))] = hashlib.sha256(
                np.ascontiguousarray(matrix).tobytes()).hexdigest()
            for name, root_update in root_constructions(matrix.astype(np.float64), rng).items():
                reference = published_fltrust(matrix, root_update)
                for method in ('fltrust_normalized', 'fltrust'):
                    outcome = server_aggregate(matrix, root_update, method)
                    rows.append(dict(ref=ref_dir.name, round=rnd, root=name, method=method,
                                     **outcome, **agreement(outcome['applied_update'],
                                                            reference['aggregate'])))
            matrices += 1
        if matrices >= 6:
            break
    for row in rows:
        row.pop('applied_update', None)
    return rows


def edge_cases():
    """Boundaries the formula comparison did not reach."""
    cases = []

    # 1. Every cosine negative, so every trust score is zero.
    updates = np.array([[-1.0, 0.0], [-2.0, 0.0]], dtype=np.float32)
    root = np.array([1.0, 0.0], dtype=np.float64)
    reference = published_fltrust(updates, root)
    outcome = server_aggregate(updates, root, 'fltrust_normalized')
    cases.append(dict(case='all_trust_zero',
                      reference_aggregate=reference['aggregate'].tolist(),
                      **outcome, **agreement(outcome['applied_update'], reference['aggregate'])))

    # 2. A zero root update: the local filter declares a degenerate root.
    updates = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    root = np.zeros(2, dtype=np.float64)
    reference = published_fltrust(updates, root)
    outcome = server_aggregate(updates, root, 'fltrust_normalized')
    cases.append(dict(case='zero_root',
                      reference_aggregate=reference['aggregate'].tolist(),
                      **outcome, **agreement(outcome['applied_update'], reference['aggregate'])))

    # 3. One client at the norm guard, one ordinary.
    updates = np.array([[1e-12, 0.0], [1.0, 0.0]], dtype=np.float32)
    root = np.array([1.0, 0.0], dtype=np.float64)
    reference = published_fltrust(updates, root)
    outcome = server_aggregate(updates, root, 'fltrust_normalized')
    cases.append(dict(case='client_norm_at_guard',
                      reference_aggregate=reference['aggregate'].tolist(),
                      **outcome, **agreement(outcome['applied_update'], reference['aggregate'])))

    # 4. One client exactly orthogonal, so its trust is exactly zero.
    updates = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    root = np.array([1.0, 0.0], dtype=np.float64)
    reference = published_fltrust(updates, root)
    outcome = server_aggregate(updates, root, 'fltrust_normalized')
    cases.append(dict(case='one_trust_exactly_zero',
                      reference_aggregate=reference['aggregate'].tolist(),
                      **outcome, **agreement(outcome['applied_update'], reference['aggregate'])))

    for case in cases:
        case.pop('applied_update', None)
    return cases


def canonical_occurrences(sources):
    """Did any of these fallback paths fire in the recorded FLTrust runs?"""
    totals = dict(runs=0, rounds=0, empty_accept_rounds=0, degraded_rounds=0,
                  fallback_rounds=0, min_accepted=None, max_rejected=None)
    for path in sorted(CANONICAL.rglob('fltrust_normalized_seed*.json')):
        payload = json.loads(path.read_text())
        if 'records' not in payload:
            continue
        sources[str(path.relative_to(ROOT))] = sha256(path)
        totals['runs'] += 1
        for record in payload['records']:
            totals['rounds'] += 1
            accepted = record['n_benign']
            totals['empty_accept_rounds'] += int(accepted == 0)
            totals['degraded_rounds'] += int(bool(record.get('degraded', 0)))
            totals['fallback_rounds'] += int(record.get('fallback_reason', 'none') != 'none')
            totals['min_accepted'] = accepted if totals['min_accepted'] is None else min(
                totals['min_accepted'], accepted)
            totals['max_rejected'] = record['n_anomaly'] if totals['max_rejected'] is None else max(
                totals['max_rejected'], record['n_anomaly'])
    return totals


def write_csv(path, records):
    if not records:
        return
    fields = list(records[0])
    with Path(path).open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for record in records:
            handle.write(','.join('' if record[f] is None else str(record[f])
                                  for f in fields) + '\n')


def main():
    sources = {}
    rows = real_path_cases(sources)
    edges = edge_cases()
    canonical = canonical_occurrences(sources)

    write_csv(HERE / 'server_path_cases.csv', rows)
    write_csv(HERE / 'edge_cases.csv',
              [{k: v for k, v in c.items() if k != 'reference_aggregate'} for c in edges])

    summary = []
    for method in ('fltrust_normalized', 'fltrust'):
        for name in ('cohort_mean', 'small', 'large', 'unrelated'):
            cell = [r for r in rows if r['method'] == method and r['root'] == name]
            if not cell:
                continue
            summary.append(dict(
                method=method, root=name, cases=len(cell),
                relative_gap_max=max(r['relative_gap'] for r in cell),
                cosine_min=min(r['cosine'] for r in cell if r['cosine'] is not None),
                accepted_min=min(r['accepted'] for r in cell),
                rejected_max=max(r['rejected'] for r in cell)))
    write_csv(HERE / 'server_path_summary.csv', summary)

    report = dict(real_path_cases=len(rows), matrices=len({(r['ref'], r['round']) for r in rows}),
                  summary=summary, edge_cases=edges, canonical=canonical)
    (HERE / 'server_path_summary.json').write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'server_path_provenance.json').write_text(json.dumps(dict(
        read_only=True, script_sha256=sha256(__file__), inputs=sources), indent=2) + '\n')
    print(json.dumps(dict(real_path_cases=len(rows),
                          matrices=report['matrices'],
                          canonical=canonical), indent=2))
    print(json.dumps(edges, indent=2))


if __name__ == '__main__':
    main()
