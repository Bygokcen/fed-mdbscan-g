import numpy as np
import pytest

from simulation.audit_attacks import constrained_poison, profile_constrained_poison
from simulation.contracts import resolve_experiment_config


def _benign(rows=12, dim=40, seed=3):
    """Mildly correlated updates: a shared descent direction plus per-client noise."""
    rng = np.random.default_rng(seed)
    return (rng.standard_normal((rows, dim)) * 0.3 + 0.05).astype(np.float32)


def _heterogeneous(rows=40, dim=40, seed=5):
    """The observed non-IID regime: individual directions largely cancel, so the
    cohort mean is a small fraction of a typical client norm and the distance
    budget carries the attacker past the origin. Calibrated against the recorded
    runs, where ||mean|| is roughly a fifth of the median client norm."""
    rng = np.random.default_rng(seed)
    updates = rng.standard_normal((rows, dim))
    updates -= updates.mean(axis=0)
    return (updates + 0.05).astype(np.float32)


def test_flat_profile_meets_its_norm_target_and_the_original_constraint():
    benign = _benign()
    target_ratio = 1.0
    poisoned, info = profile_constrained_poison(benign, target_ratio)
    assert info['constraint_achieved'] <= info['constraint_bound'] * (1 + 1e-5)
    if not info['gamma_clamped']:
        median_norm = float(np.median(np.linalg.norm(benign.astype(np.float64), axis=1)))
        assert info['realized_norm'] == pytest.approx(target_ratio * median_norm, rel=1e-5)


def test_realized_norm_stays_inside_the_range_the_constraint_allows():
    """The poisoned update is collinear with the mean, so its norm is
    |||mean|| - gamma| and gamma is capped by the distance budget. The reachable
    norms are therefore a closed interval, and the budget attack sits at one end."""
    benign = _benign()
    work = benign.astype(np.float64)
    mean_norm = float(np.linalg.norm(work.mean(axis=0)))
    budget, budget_info = constrained_poison(benign, 'minmax_omniscient')
    budget_norm = float(np.linalg.norm(budget.astype(np.float64)))

    flat, info = profile_constrained_poison(benign, 1.0)
    assert 0.0 <= info['gamma'] <= info['gamma_max'] + 1e-9
    assert info['realized_norm'] <= abs(mean_norm - info['gamma_max']) + 1e-6
    # An unreachable target falls back to the full budget, never to no attack.
    huge = profile_constrained_poison(benign, 1e9)[1]
    assert huge['gamma'] == pytest.approx(info['gamma_max'], rel=1e-9)
    assert huge['gamma_clamped'] is True
    assert budget_norm == pytest.approx(abs(mean_norm - budget_info['gamma']), rel=1e-5)


def test_flat_profile_still_points_against_the_benign_mean():
    """The camouflage must not turn the attack into a contribution: hitting the
    target norm on the near branch would leave the update aligned with the mean."""
    benign = _heterogeneous()
    mean = benign.astype(np.float64).mean(axis=0)
    poisoned, info = profile_constrained_poison(benign, 1.0)
    assert not info['gamma_clamped'], 'the heterogeneous fixture must reach the target'
    assert float(poisoned.astype(np.float64) @ mean) < 0.0
    assert info['realized_norm'] == pytest.approx(info['target_norm'], rel=1e-5)


def test_unreachable_target_falls_back_to_the_budget_attack():
    """When the constraint cannot carry the update past the mean, the variant
    must degrade to the ordinary Min-Max step rather than to no attack."""
    benign = _benign()
    budget, budget_info = constrained_poison(benign, 'minmax_omniscient')
    flat, info = profile_constrained_poison(benign, 1e9)
    assert info['gamma_clamped'] is True
    assert info['gamma'] == pytest.approx(budget_info['gamma'], rel=1e-9)
    assert np.allclose(flat, budget, rtol=1e-6, atol=1e-8)


def test_ratio_zero_is_the_most_hidden_and_stays_inside_the_constraint():
    benign = _benign()
    poisoned, info = profile_constrained_poison(benign, 0.0)
    assert info['constraint_achieved'] <= info['constraint_bound'] * (1 + 1e-5)
    assert info['gamma'] >= 0.0


def test_rejects_an_invalid_ratio_and_a_degenerate_batch():
    with pytest.raises(ValueError):
        profile_constrained_poison(_benign(), -1.0)
    with pytest.raises(ValueError):
        profile_constrained_poison(np.ones((1, 4), dtype=np.float32), 1.0)


def test_config_accepts_the_new_attack_and_validates_the_ratio():
    config = resolve_experiment_config(
        {'attack_type': 'minmax_flat_omniscient', 'coordinated_profile_ratio': 2.0})
    assert config['attack_type'] == 'minmax_flat_omniscient'
    assert config['coordinated_profile_ratio'] == 2.0
    with pytest.raises(ValueError):
        resolve_experiment_config({'coordinated_profile_ratio': -0.5})


def test_existing_coordinated_attack_is_untouched():
    benign = _benign()
    first, info = constrained_poison(benign, 'minmax_omniscient')
    second, _ = constrained_poison(benign, 'minmax_omniscient')
    assert np.array_equal(first, second)
    assert 'profile_ratio' not in info
