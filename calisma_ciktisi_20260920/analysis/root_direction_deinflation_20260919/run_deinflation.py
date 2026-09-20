"""Offline de-inflation sweep and clean false-alarm check for the root direction score.

Implements PROTOCOL.md. Read-only over the gate-v2 matrices and the root-signal
probe artifacts; trains nothing and writes only into this directory.

Part A replaces the copied Min-Max vector with per-attacker independent
directions at a fixed angular spread from the original inverse-mean direction,
re-solves the same Min-Max scalar constraint for each direction, verifies the
constraint by measurement, and re-scores with the stored root direction.

Part B standardises the recorded scores within each checkpoint without labels,
selects one threshold on the attacked Min-Max development arm only, and applies
it unchanged to the clean and patch arms.

    .venv/bin/python analysis/root_direction_deinflation_20260919/run_deinflation.py
"""

import hashlib
import json
import math
import statistics
from pathlib import Path

import numpy as np

ROOT = Path('/home/gokcen/Fed_MDBSCAN_TIFS')
HERE = Path(__file__).resolve().parent
GATE = ROOT / 'new_work/results/mechanism_gate_replay/replay_20260915_v2'
PROBE = ROOT / 'new_work/results/mechanism_root_signal/probe_20260919_v1'

ANGLES_DEG = [0, 15, 30, 45, 60, 90]
RNG_SEED = 20260919
CHECKPOINTS = (0, 9, 29)


def sha256_bytes(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


def minmax_gamma(mean, benign, direction, bound):
    """The scalar solve used by simulation.audit_attacks.constrained_poison."""
    deviations = mean - benign
    q = np.einsum('ij,ij->i', deviations, deviations)
    b = deviations @ direction
    gamma = float(np.min(-b + np.sqrt(np.maximum(b * b + bound - q, 0.0))))
    return max(0.0, gamma) * (1 - 1e-6)


def orthogonal_unit(reference, rng):
    """A unit vector orthogonal to ``reference``, drawn from a fixed stream."""
    while True:
        candidate = rng.standard_normal(reference.shape[0])
        candidate -= reference * float(candidate @ reference)
        norm = float(np.linalg.norm(candidate))
        if norm > 1e-12:
            return candidate / norm


def reference_identity(path):
    parts = Path(path).parts
    return dict(dataset=parts[2], attack=parts[3].replace('scenario_cut_', ''),
                mode='attacked' if 'cutoff_attacked' in parts[1] else 'clean',
                seed=int(Path(parts[-1]).stem.split('seed')[-1]))


def load_cells():
    """Join each root-signal reference to its gate-v2 matrices by content hash."""
    cells = []
    for ref_dir in sorted(PROBE.glob('ref_*')):
        scores_path = ref_dir / 'root_scores.json'
        validation_path = ref_dir / 'validation.json'
        if not scores_path.exists() or not validation_path.exists():
            continue
        if not json.loads(validation_path.read_text()).get('valid'):
            continue
        payload = json.loads(scores_path.read_text())
        identity = reference_identity(payload['reference']['path'])
        gate_dir = GATE / ref_dir.name
        for checkpoint in payload['checkpoints']:
            rnd = checkpoint['round']
            matrix_path = gate_dir / f'round_{rnd:02d}_updates.npy'
            direction_path = ref_dir / f'round_{rnd:02d}_root_direction.npy'
            if not matrix_path.exists() or not direction_path.exists():
                raise SystemExit(f'missing artifact for {ref_dir.name} round {rnd}')
            matrix = np.load(matrix_path)
            if sha256_bytes(matrix) != checkpoint['matrix_content_sha256']:
                raise SystemExit(f'matrix content mismatch for {ref_dir.name} round {rnd}')
            cells.append(dict(ref=ref_dir.name, round=rnd, **identity,
                              matrix=matrix,
                              root_direction=np.load(direction_path),
                              rows=checkpoint['rows'],
                              matrix_path=matrix_path,
                              direction_path=direction_path))
    return cells


def part_a(cells, sources):
    """Angular spread sweep on the attacked Min-Max checkpoints."""
    results, integrity = [], []
    for cell in cells:
        if not (cell['attack'] == 'minmax' and cell['mode'] == 'attacked'):
            continue
        sources[str(cell['matrix_path'].relative_to(ROOT))] = sha256_bytes(cell['matrix'])
        sources[str(cell['direction_path'].relative_to(ROOT))] = sha256_file(cell['direction_path'])

        rows = cell['rows']
        attacker_mask = np.array([bool(r['actual_attacker']) for r in rows])
        matrix = cell['matrix'].astype(np.float64)
        benign = matrix[~attacker_mask]
        n_attackers = int(attacker_mask.sum())

        g = cell['root_direction'].astype(np.float64)
        g_norm = float(np.linalg.norm(g))

        def score(vector):
            norm = float(np.linalg.norm(vector))
            if norm == 0 or g_norm == 0:
                return None
            return -float(vector @ g) / (norm * g_norm)

        # Honest scores must reproduce the recorded ones exactly.
        honest_recorded = [r['negative_root_cosine'] for r in rows if not r['actual_attacker']]
        honest_recomputed = [score(row) for row in benign]
        max_gap = max(abs(a - b) for a, b in zip(honest_recorded, honest_recomputed))

        mean = benign.mean(axis=0)
        mean_norm = float(np.linalg.norm(mean))
        u = -mean / mean_norm
        # ||a-b||^2 = ||a||^2 + ||b||^2 - 2 a.b keeps this a 72x72 problem
        # instead of materialising a 72x72x159010 array.
        square_norms = np.einsum('ij,ij->i', benign, benign)
        gram = benign @ benign.T
        pairwise = square_norms[:, None] + square_norms[None, :] - 2.0 * gram
        bound = float(np.maximum(pairwise, 0.0).max())

        # Integrity gate: theta = 0 must reproduce the recorded attacker score.
        recorded_attacker = next(r['negative_root_cosine'] for r in rows if r['actual_attacker'])
        replay = mean + minmax_gamma(mean, benign, u, bound) * u
        replay_gap = abs(score(replay) - recorded_attacker)
        integrity.append(dict(ref=cell['ref'], round=cell['round'],
                              honest_max_abs_gap=max_gap,
                              theta0_attacker_gap=replay_gap,
                              attackers=n_attackers))
        if replay_gap > 1e-6 or max_gap > 1e-6:
            raise SystemExit(f'integrity gate failed for {cell["ref"]} round {cell["round"]}')

        rng = np.random.default_rng(RNG_SEED)
        for degrees in ANGLES_DEG:
            theta = math.radians(degrees)
            synthetic, violations = [], 0
            for _ in range(n_attackers):
                direction = u if degrees == 0 else (
                    math.cos(theta) * u + math.sin(theta) * orthogonal_unit(u, rng))
                direction = direction / float(np.linalg.norm(direction))
                gamma = minmax_gamma(mean, benign, direction, bound)
                poisoned = mean + gamma * direction
                achieved = float(((poisoned - benign) ** 2).sum(axis=1).max())
                if achieved > bound + max(1e-10, abs(bound) * 1e-5):
                    violations += 1
                    continue
                synthetic.append(poisoned)
            attacker_scores = [score(v) for v in synthetic]
            attacker_scores = [s for s in attacker_scores if s is not None]
            results.append(dict(
                ref=cell['ref'], dataset=cell['dataset'], seed=cell['seed'],
                round=cell['round'], theta_deg=degrees,
                generated=len(synthetic), violations=violations,
                unique_scores=len({round(s, 12) for s in attacker_scores}),
                auc=auc(attacker_scores, honest_recomputed),
                attacker_median=statistics.median(attacker_scores) if attacker_scores else None,
                honest_median=statistics.median(honest_recomputed)))
    return results, integrity


def part_b(cells, sources):
    """Label-free within-checkpoint standardisation, one development threshold."""
    standardised = []
    for cell in cells:
        sources.setdefault(str((PROBE / cell['ref'] / 'root_scores.json').relative_to(ROOT)),
                           sha256_file(PROBE / cell['ref'] / 'root_scores.json'))
        values = [r['negative_root_cosine'] for r in cell['rows']]
        median = statistics.median(values)
        deviations = [abs(v - median) for v in values]
        mad = statistics.median(deviations)
        if mad == 0:
            standardised.append(dict(ref=cell['ref'], dataset=cell['dataset'],
                                     attack=cell['attack'], mode=cell['mode'],
                                     seed=cell['seed'], round=cell['round'],
                                     undefined=True, rows=[]))
            continue
        scaled = [dict(z=(v - median) / (1.4826 * mad),
                       attacker=bool(r['actual_attacker']))
                  for v, r in zip(values, cell['rows'])]
        standardised.append(dict(ref=cell['ref'], dataset=cell['dataset'],
                                 attack=cell['attack'], mode=cell['mode'],
                                 seed=cell['seed'], round=cell['round'],
                                 undefined=False, rows=scaled))

    development = [c for c in standardised
                   if c['attack'] == 'minmax' and c['mode'] == 'attacked' and not c['undefined']]
    attacker_z = [r['z'] for c in development for r in c['rows'] if r['attacker']]
    threshold = min(attacker_z) if attacker_z else None

    applied = []
    for cell in standardised:
        if cell['undefined'] or threshold is None:
            continue
        honest = [r for r in cell['rows'] if not r['attacker']]
        attackers = [r for r in cell['rows'] if r['attacker']]
        applied.append(dict(
            dataset=cell['dataset'], attack=cell['attack'], mode=cell['mode'],
            seed=cell['seed'], round=cell['round'],
            honest=len(honest), attackers=len(attackers),
            honest_flagged=sum(1 for r in honest if r['z'] >= threshold),
            attackers_flagged=sum(1 for r in attackers if r['z'] >= threshold)))
    return dict(threshold=threshold,
                threshold_origin='selected on the attacked Min-Max development arm',
                undefined_checkpoints=sum(1 for c in standardised if c['undefined']),
                rows=applied)


def write_csv(path, records):
    if not records:
        return
    fields = list(records[0])
    with Path(path).open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for record in records:
            handle.write(','.join(
                '' if record[f] is None else str(record[f]) for f in fields) + '\n')


def main():
    sources = {}
    cells = load_cells()
    sweep, integrity = part_a(cells, sources)
    clean = part_b(cells, sources)

    write_csv(HERE / 'sweep_by_checkpoint.csv', sweep)
    write_csv(HERE / 'integrity.csv', integrity)
    write_csv(HERE / 'threshold_applied.csv', clean['rows'])

    by_angle = []
    for degrees in ANGLES_DEG:
        for dataset in sorted({s['dataset'] for s in sweep}):
            cell = [s for s in sweep if s['theta_deg'] == degrees and s['dataset'] == dataset]
            values = [s['auc'] for s in cell if s['auc'] is not None]
            by_angle.append(dict(
                dataset=dataset, theta_deg=degrees, checkpoints=len(cell),
                auc_median=statistics.median(values) if values else None,
                auc_min=min(values) if values else None,
                auc_max=max(values) if values else None,
                violations=sum(s['violations'] for s in cell),
                unique_scores_median=statistics.median([s['unique_scores'] for s in cell])))
    write_csv(HERE / 'sweep_by_angle.csv', by_angle)

    summary = dict(checkpoints=len(cells),
                   minmax_attacked_checkpoints=len({(s['ref'], s['round']) for s in sweep}),
                   angles=ANGLES_DEG, rng_seed=RNG_SEED,
                   integrity_max_honest_gap=max(i['honest_max_abs_gap'] for i in integrity),
                   integrity_max_theta0_gap=max(i['theta0_attacker_gap'] for i in integrity),
                   by_angle=by_angle, clean_check=clean)
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (HERE / 'provenance.json').write_text(json.dumps(dict(
        read_only=True, script_sha256=sha256_file(__file__),
        protocol_sha256=sha256_file(HERE / 'PROTOCOL.md'), inputs=sources), indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('by_angle', 'clean_check')},
                     indent=2))


if __name__ == '__main__':
    main()
