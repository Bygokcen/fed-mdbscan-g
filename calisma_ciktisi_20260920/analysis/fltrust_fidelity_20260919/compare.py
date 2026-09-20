"""FLTrust implementation fidelity: the local rule against the published one.

Feeds identical inputs -- the same client updates and the same root update --
to two rules and compares trust scores, magnitude scaling, weights and the
combined update, as the review protocol asks.

The reference rule is transcribed from the authors' demo archive
(`author_code_provenance.json` records its URL, hashes and the absence of any
licence). That archive is MXNet and is **not redistributed here**; what follows
is this project's own NumPy statement of the published formula, written so the
arithmetic can be checked against the paper.

Client updates come from the recorded gate-v2 checkpoint matrices, so the inputs
are real updates rather than synthetic ones. A root update is required as well;
the archives do not store one, so several constructions are used and the rules
are compared under each. Rule fidelity does not depend on where the root update
comes from, as long as both rules receive the same one -- how the root update is
produced is a separate comparison axis, noted in the report.

    .venv/bin/python analysis/fltrust_fidelity_20260919/compare.py

Read-only: writes only into this directory.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path('/home/gokcen/Fed_MDBSCAN_TIFS')
HERE = Path(__file__).resolve().parent
GATE = ROOT / 'new_work/results/mechanism_gate_replay/replay_20260915_v2'
sys.path.insert(0, str(ROOT / 'new_work'))

EPS_AUTHOR = 1e-9          # additive, as published
EPS_LOCAL = 1e-10          # threshold guard, as implemented here


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ----------------------------------------------------------------------
# Published rule (Cao et al., NDSS 2021), stated in NumPy
# ----------------------------------------------------------------------
def published_fltrust(updates, root_update):
    """Trust-weighted aggregation exactly as the demo archive computes it.

    Every client is rescaled to the root norm, whether it is larger or smaller;
    the trust scores are normalised to sum to one before the weighted sum; and
    a client whose cosine is non-positive receives weight zero rather than being
    removed from the cohort.
    """
    baseline = np.asarray(root_update, dtype=np.float64)
    matrix = np.asarray(updates, dtype=np.float64)
    baseline_norm = float(np.linalg.norm(baseline))
    norms = np.linalg.norm(matrix, axis=1)

    cosine = (matrix @ baseline) / (baseline_norm + EPS_AUTHOR) / (norms + EPS_AUTHOR)
    trust = np.maximum(cosine, 0.0)
    weights = trust / (trust.sum() + EPS_AUTHOR)
    scaled = matrix * (baseline_norm / (norms + EPS_AUTHOR))[:, None]
    aggregate = (weights[:, None] * scaled).sum(axis=0)
    return dict(cosine=cosine, trust=trust, weights=weights,
                scaled_norms=np.linalg.norm(scaled, axis=1), aggregate=aggregate,
                rejected=np.zeros(len(matrix), dtype=bool))


# ----------------------------------------------------------------------
# Local rule, as this project implements it
# ----------------------------------------------------------------------
def local_fltrust(updates, root_update, always_normalise):
    """The local filter plus the server-side aggregation it signals.

    ``always_normalise`` selects between the two registered methods:
    ``fltrust_normalized`` rescales every kept update, while ``fltrust``
    rescales only those whose norm exceeds the root norm.
    """
    from simulation.baselines import fltrust as local_filter

    matrix = np.asarray(updates)
    kept, dropped, info = local_filter(matrix, np.asarray(root_update))
    cosine = np.asarray(info['cos_sims'], dtype=np.float64)
    trust = np.asarray(info['trust_weights'], dtype=np.float64)
    root_norm = float(info['root_norm'])

    work = matrix.astype(np.float64)
    scaled = work.copy()
    weighted_sum = np.zeros(work.shape[1], dtype=np.float64)
    total = 0.0
    for index in kept:
        vector = work[index]
        norm = float(np.linalg.norm(vector))
        if norm > EPS_LOCAL and (norm > root_norm or always_normalise):
            vector = vector * (root_norm / norm)
        scaled[index] = vector
        weighted_sum += trust[index] * vector
        total += trust[index]
    aggregate = weighted_sum / total if total > EPS_LOCAL else work.mean(axis=0)

    weights = np.zeros(len(work))
    if total > EPS_LOCAL:
        for index in kept:
            weights[index] = trust[index] / total
    rejected = np.ones(len(work), dtype=bool)
    rejected[list(kept)] = False
    return dict(cosine=cosine, trust=trust, weights=weights,
                scaled_norms=np.linalg.norm(scaled, axis=1), aggregate=aggregate,
                rejected=rejected)


def compare(a, b):
    def gap(key):
        return float(np.max(np.abs(np.asarray(a[key]) - np.asarray(b[key]))))

    # Scaling is only meaningful where a client actually contributes: the local
    # rule leaves zero-trust rows untouched, the published one rescales them,
    # and both give them weight zero, so comparing those rows says nothing.
    contributing = np.asarray(b['trust']) > 0
    if contributing.any():
        scaled_gap = float(np.max(np.abs(
            np.asarray(a['scaled_norms'])[contributing]
            - np.asarray(b['scaled_norms'])[contributing])))
    else:
        scaled_gap = 0.0
    left, right = np.asarray(a['aggregate']), np.asarray(b['aggregate'])
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    cosine = float(left @ right / denominator) if denominator else None
    return dict(
        cosine_max_gap=gap('cosine'),
        trust_max_gap=gap('trust'),
        weight_max_gap=gap('weights'),
        scaled_norm_max_gap=scaled_gap,
        aggregate_max_gap=gap('aggregate'),
        aggregate_relative_gap=float(np.linalg.norm(left - right) / (np.linalg.norm(right) or 1.0)),
        aggregate_cosine=cosine,
        zero_trust_clients=int((np.asarray(b['trust']) <= 0).sum()),
        clients_the_local_rule_removes=int(np.asarray(a['rejected']).sum()))


def root_constructions(matrix, rng):
    """Root updates to test the rule under. Both rules always receive the same one."""
    mean = matrix.mean(axis=0)
    unit = rng.standard_normal(matrix.shape[1])
    unit /= np.linalg.norm(unit)
    return {
        # A root update aligned with the cohort, at a typical client magnitude.
        'cohort_mean': mean / (np.linalg.norm(mean) or 1.0) * float(np.median(np.linalg.norm(matrix, axis=1))),
        # A small root update, so that every client norm exceeds it.
        'small': mean / (np.linalg.norm(mean) or 1.0) * float(np.min(np.linalg.norm(matrix, axis=1))) * 0.5,
        # A large root update, so that no client norm reaches it.
        'large': mean / (np.linalg.norm(mean) or 1.0) * float(np.max(np.linalg.norm(matrix, axis=1))) * 2.0,
        # An unrelated direction, to exercise negative cosines.
        'unrelated': unit * float(np.median(np.linalg.norm(matrix, axis=1))),
    }


def main():
    rows, sources = [], {}
    rng = np.random.default_rng(20260919)
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
                for variant, always in (('fltrust_normalized', True), ('fltrust', False)):
                    local = local_fltrust(matrix, root_update, always)
                    rows.append(dict(ref=ref_dir.name, round=rnd, root=name,
                                     variant=variant, clients=len(matrix),
                                     **compare(local, reference)))
        if len(rows) >= 4 * 2 * 3 * 6:   # six references is enough to characterise
            break

    fields = list(rows[0])
    with (HERE / 'per_case.csv').open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in rows:
            handle.write(','.join('' if row[f] is None else str(row[f]) for f in fields) + '\n')

    summary = []
    for variant in ('fltrust_normalized', 'fltrust'):
        for name in ('cohort_mean', 'small', 'large', 'unrelated'):
            cell = [r for r in rows if r['variant'] == variant and r['root'] == name]
            if not cell:
                continue
            summary.append(dict(
                variant=variant, root=name, cases=len(cell),
                trust_max_gap=max(r['trust_max_gap'] for r in cell),
                weight_max_gap=max(r['weight_max_gap'] for r in cell),
                scaled_norm_max_gap=max(r['scaled_norm_max_gap'] for r in cell),
                aggregate_relative_gap_max=max(r['aggregate_relative_gap'] for r in cell),
                aggregate_cosine_min=min(r['aggregate_cosine'] for r in cell
                                         if r['aggregate_cosine'] is not None),
                zero_trust_clients=max(r['zero_trust_clients'] for r in cell),
                removed_by_local_rule=max(r['clients_the_local_rule_removes'] for r in cell)))

    fields = list(summary[0])
    with (HERE / 'summary.csv').open('w') as handle:
        handle.write(','.join(fields) + '\n')
        for row in summary:
            handle.write(','.join(str(row[f]) for f in fields) + '\n')

    report = dict(cases=len(rows), summary=summary)
    (HERE / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    (HERE / 'provenance.json').write_text(json.dumps(dict(
        read_only=True, script_sha256=sha256(__file__),
        author_code=json.loads((HERE / 'author_code_provenance.json').read_text()),
        inputs=sources), indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
