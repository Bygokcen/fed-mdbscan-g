import json

import numpy as np
import pytest

from simulation.contracts import (
    aggregate_accepted_updates,
    apply_lognormal_retention,
    expected_participation,
    resolve_experiment_config,
    stealth_gaussian_perturbation,
)


def test_resolved_config_is_complete_round_trippable_and_digest_is_stable():
    first = resolve_experiment_config({"num_clients": 12, "stealth_rho": 0.005})
    reordered = resolve_experiment_config({"stealth_rho": 0.005, "num_clients": 12})

    assert first == reordered
    assert first["protocol_digest"] == reordered["protocol_digest"]
    assert first["schema_version"] == "fed-mdbscan-g-unit-v2"
    assert first["protocol_version"] == "audit-contract-v2"
    assert first["aggregation_operator"] == "uniform_mean"
    assert first["empty_client_policy"] == "preserve_empty"
    assert first["stealth_rho_sensitivity"] == [0.001, 0.01]
    assert first["num_classes"] == 10
    assert first["optimizer_momentum"] == 0.9
    assert first["test_batch_size"] == 128
    assert first["root_batch_size"] == 32
    assert resolve_experiment_config(json.loads(json.dumps(first))) == first


@pytest.mark.parametrize("shape", [(7,), (2, 3), (2, 2, 2)])
def test_stealth_gaussian_uses_total_l2_budget_and_preserves_geometry(shape):
    gradient = np.arange(1, np.prod(shape) + 1, dtype=np.float32).reshape(shape)
    attacked = stealth_gaussian_perturbation(
        gradient, rho=0.005, rng=np.random.default_rng(19)
    )

    assert attacked.shape == gradient.shape
    assert attacked.dtype == gradient.dtype
    assert np.linalg.norm(attacked - gradient) == pytest.approx(
        0.005 * np.linalg.norm(gradient), rel=2e-5, abs=1e-8
    )


def test_stealth_gaussian_zero_is_unchanged_and_invalid_inputs_fail_closed():
    zero = np.zeros((3, 2), dtype=np.float64)
    assert np.array_equal(stealth_gaussian_perturbation(zero), zero)

    for invalid in (
        np.array([1.0, np.nan]),
        np.array([1.0, np.inf]),
        np.array([1, 2], dtype=np.int64),
        np.array([1 + 2j], dtype=np.complex128),
        np.array([], dtype=np.float32),
    ):
        with pytest.raises(ValueError):
            stealth_gaussian_perturbation(invalid)
    for rho in (-0.1, np.nan, np.inf):
        with pytest.raises(ValueError):
            stealth_gaussian_perturbation(np.ones(3, dtype=np.float32), rho=rho)


def test_lognormal_retention_is_deterministic_preserves_empty_and_respects_floor():
    original = {0: list(range(10)), 1: [], 2: list(range(10, 30))}
    first = apply_lognormal_retention(
        original, sigma=0.8, min_samples=6, seed=23,
        empty_client_policy="preserve_empty",
    )
    second = apply_lognormal_retention(
        original, sigma=0.8, min_samples=6, seed=23,
        empty_client_policy="preserve_empty",
    )

    assert first == second
    assert first[1] == []
    assert all(len(first[cid]) >= min(6, len(indices))
               for cid, indices in original.items() if indices)
    assert all(set(first[cid]).issubset(indices)
               for cid, indices in original.items())
    reordered = apply_lognormal_retention(
        dict(reversed(list(original.items()))), sigma=0.8, min_samples=6, seed=23,
        empty_client_policy="preserve_empty",
    )
    assert reordered == first


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sigma": -0.1},
        {"sigma": np.nan},
        {"min_samples": -1},
        {"min_samples": 1.5},
        {"empty_client_policy": "invent_samples"},
    ],
)
def test_lognormal_retention_rejects_invalid_contract(kwargs):
    with pytest.raises((TypeError, ValueError)):
        apply_lognormal_retention({0: [1, 2]}, **kwargs)


def test_participation_contract_names_dropout_and_expected_count_explicitly():
    resolved = resolve_experiment_config(
        {"num_clients": 100, "malicious_ratio": 0.2, "dropout_rate": 0.1}
    )
    counts = expected_participation(resolved)
    assert counts == {
        "active_clients": 100,
        "benign_clients": 82,
        "malicious_clients": 18,
        "expected_benign_participants": 72.0,
        "expected_total_participants": 90.0,
        "malicious_participation_policy": "always_participate",
    }

    with pytest.raises(ValueError):
        resolve_experiment_config({"dropout_rate": 1.1})


@pytest.mark.parametrize(
    "override",
    [
        {"steath_rho": 0.1},
        {"method_params": {"fed_mdbscan_g": {"unknown": 1}}},
        {"attack_type": "silent_noop"},
        {"seed": -1},
        {"seed": 2**32},
        {"iid": 1},
        {"schema_version": "forged"},
    ],
)
def test_resolver_rejects_unknown_or_ambiguous_contract_values(override):
    with pytest.raises((TypeError, ValueError)):
        resolve_experiment_config(override)


def test_label_flip_class_count_is_resolved_before_digest():
    mnist = resolve_experiment_config({"dataset": "mnist", "attack_type": "label_flip"})
    har = resolve_experiment_config({"dataset": "har", "attack_type": "label_flip"})
    assert mnist["num_classes"] == 10
    assert har["num_classes"] == 6
    assert mnist["protocol_digest"] != har["protocol_digest"]


def test_weighted_aggregation_allows_rejected_empty_client_only():
    updates = np.array([[1.0, 3.0], [9.0, 9.0]], dtype=np.float32)
    result = aggregate_accepted_updates(
        updates, [0], operator="sample_weighted_mean", sample_counts=[4, 0],
    )
    assert np.allclose(result, updates[0])
    with pytest.raises(ValueError, match="positive total"):
        aggregate_accepted_updates(
            updates, [1], operator="sample_weighted_mean", sample_counts=[4, 0],
        )


def test_attack_overflow_fails_closed():
    huge = np.array([np.finfo(np.float64).max, np.finfo(np.float64).max])
    with pytest.raises(ValueError):
        stealth_gaussian_perturbation(huge, rho=np.finfo(np.float64).max)
