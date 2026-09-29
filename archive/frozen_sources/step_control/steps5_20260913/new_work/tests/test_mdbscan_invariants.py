import numpy as np
import pytest

from simulation.mdbscan import (
    _geometric_trust_region_filter,
    fed_mdbscan_g_filter,
)


def _fixture():
    return np.array(
        [
            [0.00, 0.00],
            [0.02, -0.01],
            [-0.01, 0.02],
            [0.01, 0.01],
            [-0.02, -0.01],
            [0.00, -0.02],
            [7.0, 7.0],
            [7.2, 6.8],
        ],
        dtype=np.float64,
    )


def test_fed_mdbscan_g_is_client_order_invariant():
    gradients = _fixture()
    accepted, rejected, _ = fed_mdbscan_g_filter(gradients)
    permutation = np.array([6, 2, 0, 7, 4, 1, 5, 3])
    permuted_accepted, permuted_rejected, _ = fed_mdbscan_g_filter(
        gradients[permutation],
    )
    restored_accepted = {int(permutation[index]) for index in permuted_accepted}
    restored_rejected = {int(permutation[index]) for index in permuted_rejected}
    assert restored_accepted == set(accepted)
    assert restored_rejected == set(rejected)


@pytest.mark.parametrize("count", [1, 2])
def test_small_cohorts_have_explicit_degraded_fallback(count):
    gradients = np.ones((count, 3), dtype=np.float32)
    accepted, rejected, info = fed_mdbscan_g_filter(gradients)
    assert accepted == list(range(count))
    assert rejected == []
    assert info["fallback_applied"] is True
    assert info["fallback_reason"] == "cohort_below_minimum"
    assert info["degraded"] is True


def test_l2_never_readmits_an_l0_rejection_and_outputs_are_finite():
    gradients = _fixture()
    l0_accepted, _ = _geometric_trust_region_filter(gradients, threshold_factor=2.5)
    accepted, rejected, info = fed_mdbscan_g_filter(
        gradients,
        trust_region_factor=2.5,
        gap_concentration_threshold=1.0,
    )
    assert set(accepted).issubset(l0_accepted)
    assert set(accepted).isdisjoint(rejected)
    assert set(accepted) | set(rejected) == set(range(len(gradients)))
    assert np.isfinite(info["gap_concentration"])
    assert info.get("fallback_reason", "none") in {
        "none", "l2_below_safety_valve",
    }


def test_dense_coalition_and_benign_fragmentation_remain_auditable():
    gradients = np.vstack(
        [
            _fixture(),
            np.array([[0.6, 0.6], [0.65, 0.55]], dtype=np.float64),
        ]
    )
    accepted, rejected, info = fed_mdbscan_g_filter(
        gradients, gap_concentration_threshold=1.0,
    )
    assert set(accepted) | set(rejected) == set(range(len(gradients)))
    for key in (
        "layer_used", "l0_rejected_count", "l2_rejected_count",
        "natural_clusters_count", "rejected_snnc_clusters",
        "fallback_applied", "fallback_reason", "degraded",
    ):
        assert key in info
