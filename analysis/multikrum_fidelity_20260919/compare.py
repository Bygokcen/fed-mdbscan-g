"""Multi-Krum fidelity: the local selection against the published rule.

Builds on `analysis/baseline_fidelity_20260914`, which established that the
method registered as `krum_bound30` is Multi-Krum rather than Krum. This check
takes each element the review asked about -- the score, the choice of f and m,
the neighbour count, the distance, tie handling, and the validity condition --
and compares them through the real `Server.aggregate`, not a restated formula.

Reference: Blanchard, El Mhamdi, Guerraoui, Stainer, NeurIPS 2017. The score of
a vector is the sum of squared distances to its n-f-2 closest others; Krum takes
the single minimiser, Multi-Krum averages the m best, and the guarantee is
stated under 2f + 2 < n.

    .venv/bin/python analysis/multikrum_fidelity_20260919/compare.py

Read-only over the archives; writes only into this directory.
"""

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path('/home/gokcen/Fed_MDBSCAN_TIFS')
HERE = Path(__file__).resolve().parent
GATE = ROOT / 'new_work/results/mechanism_gate_replay/replay_20260915_v2'
CANONICAL = ROOT / 'new_work/results/validated/audit-v2/full_20260910/runs'
sys.path.insert(0, str(ROOT / 'new_work'))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def published_multikrum(updates, f, m):
    """Blanchard et al.'s rule, stated directly.

    Distances are computed in float64 from the given vectors, the score sums the
    n-f-2 smallest of them, and selection takes the m smallest scores with ties
    resolved by the lowest index so the result is deterministic.
    """
    matrix = np.asarray(updates, dtype=np.float64)
    n = len(matrix)
    neighbours = n - f - 2
    valid = (2 * f + 2 < n) and neighbours >= 1
    if neighbours < 1:
        return dict(valid=False, reason='no neighbours left', scores=None, selected=None)

    square_norms = np.einsum('ij,ij->i', matrix, matrix)
    distances = square_norms[:, None] + square_norms[None, :] - 2.0 * (matrix @ matrix.T)
    np.fill_diagonal(distances, np.inf)
    distances = np.maximum(distances, 0.0)
    np.fill_diagonal(distances, np.inf)
    scores = np.sort(distances, axis=1)[:, :neighbours].sum(axis=1)

    order = sorted(range(n), key=lambda i: (scores[i], i))
    selected = sorted(order[:m])
    return dict(valid=valid, reason='' if valid else 'guarantee needs 2f + 2 < n',
                scores=scores, selected=selected, neighbours=neighbours)


def server_selection(updates, max_attack_ratio=0.3):
    """Run the real server so the filter and aggregation branch are the live ones."""
    import torch
    from simulation.server import Server

    matrix = np.asarray(updates, dtype=np.float32)
    model = torch.nn.Linear(matrix.shape[1], 1, bias=False)
    with torch.no_grad():
        model.weight.zero_()
    server = Server(model=model, test_loader=[], aggregation_method='krum_bound30',
                    method_params={'max_attack_ratio': max_attack_ratio,
                                   'multi_krum_m': None})
    before = server.get_global_weights()
    result = server.aggregate([row.copy() for row in matrix],
                              participating_ids=list(range(len(matrix))), round_id=0)
    after = server.get_global_weights()
    info = result['filter_info']
    return dict(selected=sorted(result['decision']['accepted_ids']),
                applied_update=after - before,
                m=info.get('m'), f_assumed=info.get('f_assumed'),
                operator=result['decision']['aggregation_operator'],
                fallback_reason=info.get('fallback_reason', 'none'),
                degraded=bool(info.get('degraded', False)))


def local_f_and_m(n, max_attack_ratio=0.3):
    """Reproduce how the local code derives f, the neighbour count and m."""
    requested = int(math.ceil(n * max_attack_ratio))
    f = min(requested, max(0, n - 3))
    neighbours = max(1, n - f - 2)
    return dict(requested_f=requested, f=f, neighbours=neighbours, m=neighbours,
                f_was_clamped=f != requested,
                neighbours_were_clamped=(n - f - 2) < 1,
                paper_validity_holds=(2 * f + 2 < n),
                paper_experiment_m=n - f)


def main():
    sources, rows = {}, []
    matrices = 0
    for ref_dir in sorted(GATE.glob('ref_*')):
        for rnd in (0, 9, 29):
            path = ref_dir / f'round_{rnd:02d}_updates.npy'
            if not path.exists():
                continue
            matrix = np.load(path)
            sources[str(path.relative_to(ROOT))] = hashlib.sha256(
                np.ascontiguousarray(matrix).tobytes()).hexdigest()
            derived = local_f_and_m(len(matrix))
            reference = published_multikrum(matrix, derived['f'], derived['m'])
            server = server_selection(matrix)

            reference_set = set(reference['selected'])
            server_set = set(server['selected'])
            # When the differing members are tied duplicates the mean is the
            # same, so the aggregate decides whether the difference matters.
            work = matrix.astype(np.float64)
            reference_mean = work[sorted(reference_set)].mean(axis=0)
            applied = np.asarray(server['applied_update'], dtype=np.float64)
            aggregate_gap = float(np.linalg.norm(applied - reference_mean)
                                  / (np.linalg.norm(reference_mean) or 1.0))
            scores = reference['scores']
            cutoff = np.sort(scores)[derived['m'] - 1]
            tied = int(np.sum(np.isclose(scores, cutoff, rtol=0, atol=1e-9)))
            ranks = {int(i): r for r, i in enumerate(sorted(range(len(scores)),
                                                            key=lambda i: (scores[i], i)))}
            tied_ids = [i for i in range(len(scores))
                        if np.isclose(scores[i], cutoff, rtol=0, atol=1e-9)]
            straddles = bool(tied_ids and min(ranks[i] for i in tied_ids) < derived['m']
                             <= max(ranks[i] for i in tied_ids))
            # What the paper's own experiment would have selected, m = n - f.
            paper_m = published_multikrum(matrix, derived['f'], derived['paper_experiment_m'])
            rows.append(dict(
                ref=ref_dir.name, round=rnd, clients=len(matrix),
                f=derived['f'], neighbours=derived['neighbours'], m=derived['m'],
                paper_experiment_m=derived['paper_experiment_m'],
                validity_holds=derived['paper_validity_holds'],
                server_m=server['m'], server_f=server['f_assumed'],
                selection_identical=reference_set == server_set,
                selection_symmetric_difference=len(reference_set ^ server_set),
                tied_at_cutoff=tied, tie_straddles_cutoff=straddles,
                aggregate_relative_gap=aggregate_gap,
                overlap_with_paper_m=len(server_set & set(paper_m['selected'])),
                operator=server['operator'], fallback_reason=server['fallback_reason']))
            matrices += 1
        if matrices >= 6:
            break

    edge = []
    rng = np.random.default_rng(20260919)

    def record(case, updates, ratio=0.3, note=''):
        updates = np.asarray(updates, dtype=np.float32)
        derived = local_f_and_m(len(updates), ratio)
        reference = published_multikrum(updates, derived['f'], derived['m'])
        try:
            server = server_selection(updates, ratio)
            failure = ''
        except Exception as exc:                       # noqa: BLE001 - recorded, not raised
            server, failure = None, repr(exc)
        edge.append(dict(
            case=case, clients=len(updates), note=note,
            requested_f=derived['requested_f'], f=derived['f'],
            f_was_clamped=derived['f_was_clamped'],
            neighbours_were_clamped=derived['neighbours_were_clamped'],
            paper_validity_holds=derived['paper_validity_holds'],
            reference_valid=reference['valid'], reference_reason=reference['reason'],
            server_selected=len(server['selected']) if server else None,
            server_operator=server['operator'] if server else None,
            server_fallback=server['fallback_reason'] if server else None,
            selection_identical=(None if server is None or reference['selected'] is None
                                 else set(server['selected']) == set(reference['selected'])),
            server_error=failure))

    base = rng.standard_normal((20, 8))
    record('ordinary_cohort', base, note='20 clients, validity satisfied')
    record('two_clients', base[:2], note='below the rule, filter short-circuits')
    record('three_clients', base[:3], note='smallest cohort the rule admits')
    # 2f + 2 >= n: the paper's guarantee does not hold.
    record('validity_violated', base[:6], ratio=0.49, note='2f + 2 >= n')
    # Exact duplicates give identical scores, so the tie rule decides.
    tied = np.vstack([base[:4], base[:4]])
    record('exact_ties', tied, note='duplicate rows produce equal scores')
    # A cohort so small that the neighbour count would fall below one.
    record('neighbour_clamp', base[:4], ratio=0.49, note='n - f - 2 would be < 1')

    canonical = dict(runs=0, rounds=0, cohort_sizes=set(), validity_violations=0,
                     rounds_below_three=0, degraded_rounds=0, fallback_rounds=0,
                     selected_counts=set())
    for path in sorted(CANONICAL.rglob('krum_bound30_seed*.json')):
        payload = json.loads(path.read_text())
        if 'records' not in payload:
            continue
        sources[str(path.relative_to(ROOT))] = sha256(path)
        canonical['runs'] += 1
        for record_item in payload['records']:
            canonical['rounds'] += 1
            n = len(record_item['server_input_ids'])
            canonical['cohort_sizes'].add(n)
            canonical['selected_counts'].add(record_item['n_benign'])
            derived = local_f_and_m(n)
            canonical['validity_violations'] += int(not derived['paper_validity_holds'])
            canonical['rounds_below_three'] += int(n < 3)
            canonical['degraded_rounds'] += int(bool(record_item.get('degraded', 0)))
            canonical['fallback_rounds'] += int(
                record_item.get('fallback_reason', 'none') != 'none')
    canonical['cohort_sizes'] = sorted(canonical['cohort_sizes'])
    canonical['selected_counts'] = sorted(canonical['selected_counts'])

    def write_csv(path, records):
        # Notes contain commas, so the csv module does the quoting.
        if not records:
            return
        with Path(path).open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)

    write_csv(HERE / 'per_matrix.csv', rows)
    write_csv(HERE / 'edge_cases.csv', edge)
    report = dict(matrices=len(rows), edge_cases=edge, canonical=canonical,
                  all_selections_identical=all(r['selection_identical'] for r in rows))
    (HERE / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'provenance.json').write_text(json.dumps(dict(
        read_only=True, script_sha256=sha256(__file__), inputs=sources), indent=2) + '\n')
    print(json.dumps(dict(matrices=report['matrices'],
                          all_selections_identical=report['all_selections_identical'],
                          canonical=canonical), indent=2))


if __name__ == '__main__':
    main()
