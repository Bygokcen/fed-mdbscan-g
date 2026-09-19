"""Explicit audit probes; omniscient attacks are separate from gray-box noise.

Min-Max / Min-Sum constraints: Shejwalkar & Houmansadr, NDSS 2021,
https://www.ndss-symposium.org/wp-content/uploads/ndss2021_6C-3_24498_paper.pdf
The inverse mean unit direction is fixed before solving the scalar constraint.
"""
import numpy as np
from scipy.spatial.distance import cdist


def constrained_poison(benign_updates, kind='minmax_omniscient'):
    updates = np.asarray(benign_updates)
    if updates.ndim != 2 or len(updates) < 2 or not np.isfinite(updates).all():
        raise ValueError('coordinated attack needs at least two finite benign updates')
    work = updates.astype(np.float64)
    mean = work.mean(axis=0)
    norm = np.linalg.norm(mean)
    if norm == 0:
        return mean.astype(updates.dtype), {'gamma': 0., 'degenerate_mean': True}
    direction = -mean / norm
    distances = cdist(work, work, metric='sqeuclidean')
    deviations = mean - work
    q = np.einsum('ij,ij->i', deviations, deviations)
    b = deviations @ direction
    if kind == 'minmax_omniscient':
        bound = float(distances.max())
        gamma = float(np.min(-b + np.sqrt(np.maximum(b*b + bound - q, 0))))
    elif kind == 'minsum_omniscient':
        bound = float(distances.sum(axis=1).min())
        bb = float(b.sum()) / len(work)
        gamma = float(-bb + np.sqrt(max(0, bb*bb + (bound-q.sum())/len(work))))
    else:
        raise ValueError('unknown coordinated attack')
    # Stay inside the boundary after casting back to the model dtype.
    gamma = max(0., gamma) * (1 - 1e-6)
    poisoned = (mean + gamma * direction).astype(updates.dtype)
    achieved_distances = np.square(poisoned.astype(np.float64) - work).sum(axis=1)
    achieved = float(achieved_distances.max() if kind == 'minmax_omniscient' else achieved_distances.sum())
    if achieved > bound + max(1e-10, abs(bound)*1e-5):
        raise ValueError('coordinated attack violated its distance constraint')
    return poisoned, {'gamma': gamma, 'constraint_bound': bound,
                      'constraint_achieved': achieved, 'benign_reference_count': len(work),
                      'knowledge': 'omniscient_benign_updates', 'direction': 'inverse_mean_unit'}


def profile_constrained_poison(benign_updates, ratio=1.0):
    """Min-Max with the scale chosen to hide the update's norm profile.

    ``constrained_poison`` spends the whole distance budget, which makes the
    attacker's norm grow relative to the cohort as training converges. This
    variant keeps the same inverse-mean direction and the same constraint, but
    solves the scalar so that the submitted norm sits at ``ratio`` times the
    median benign norm. Because the poisoned update is collinear with the mean,
    ``||mean + gamma*u|| = |||mean|| - gamma||``, so the solve is exact.

    A smaller scalar is always inside the ball the constraint defines, so the
    result stays a valid Min-Max update; the caller still measures it.
    """
    updates = np.asarray(benign_updates)
    if updates.ndim != 2 or len(updates) < 2 or not np.isfinite(updates).all():
        raise ValueError('coordinated attack needs at least two finite benign updates')
    if not np.isfinite(ratio) or ratio < 0:
        raise ValueError('profile ratio must be a finite non-negative number')
    work = updates.astype(np.float64)
    mean = work.mean(axis=0)
    mean_norm = float(np.linalg.norm(mean))
    if mean_norm == 0:
        return mean.astype(updates.dtype), {'gamma': 0., 'degenerate_mean': True}
    direction = -mean / mean_norm
    distances = cdist(work, work, metric='sqeuclidean')
    deviations = mean - work
    q = np.einsum('ij,ij->i', deviations, deviations)
    b = deviations @ direction
    bound = float(distances.max())
    gamma_max = float(np.min(-b + np.sqrt(np.maximum(b*b + bound - q, 0))))
    gamma_max = max(0., gamma_max) * (1 - 1e-6)

    target_norm = float(ratio) * float(np.median(np.linalg.norm(work, axis=1)))
    # ||mean + gamma*u|| = |||mean|| - gamma|, a V in gamma, so a target norm has
    # two solutions. The near branch (gamma < ||mean||) leaves the update pointing
    # along +mean, which helps training instead of attacking. The adversary takes
    # the far branch, which keeps the inverse-mean direction and still hits the
    # target; it falls back to the full budget when the target is out of reach.
    requested = mean_norm + target_norm
    gamma = float(min(requested, gamma_max))
    poisoned = (mean + gamma * direction).astype(updates.dtype)

    achieved_distances = np.square(poisoned.astype(np.float64) - work).sum(axis=1)
    achieved = float(achieved_distances.max())
    if achieved > bound + max(1e-10, abs(bound)*1e-5):
        raise ValueError('coordinated attack violated its distance constraint')
    realized = float(np.linalg.norm(poisoned.astype(np.float64)))
    return poisoned, {'gamma': gamma, 'gamma_max': gamma_max,
                      'gamma_clamped': bool(requested > gamma_max),
                      'constraint_bound': bound, 'constraint_achieved': achieved,
                      'target_norm': target_norm, 'realized_norm': realized,
                      'benign_reference_count': len(work), 'profile_ratio': float(ratio),
                      'knowledge': 'omniscient_benign_updates', 'direction': 'inverse_mean_unit'}


def stamp_trigger(data, dataset, size=3):
    """White bottom-right square in normalized image coordinates; returns a copy."""
    stats = {'mnist': ([.1307], [.3081]), 'fashion_mnist': ([.2860], [.3530]),
             'cifar10': ([.4914, .4822, .4465], [.2023, .1994, .2010])}
    if dataset not in stats or data.ndim != 4 or min(data.shape[-2:]) < size:
        raise ValueError('patch trigger needs a supported image dataset')
    means, stds = stats[dataset]
    out = data.clone()
    for channel, (mean, std) in enumerate(zip(means, stds)):
        out[:, channel, -size:, -size:] = (1.0-mean)/std
    return out
