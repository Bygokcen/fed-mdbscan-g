from pathlib import Path

import numpy as np
import pytest
import torch

import simulation.server as server_module
from simulation.client import Client
from simulation.contracts import (
    aggregate_accepted_updates,
    resolve_experiment_config,
    validate_update_batch,
)
from simulation.metrics import evaluate_attack_alert, evaluate_detection_decision
from simulation.server import Server


def _server(method="fedavg", fallback_policy="accept_all_degraded"):
    model = torch.nn.Linear(2, 1, bias=False)
    return Server(
        model=model,
        test_loader=[],
        aggregation_method=method,
        fallback_policy=fallback_policy,
    )


def test_uniform_and_weighted_aggregation_are_distinct_explicit_operators():
    updates = np.array([[1.0, 3.0], [5.0, 7.0]], dtype=np.float32)
    uniform = aggregate_accepted_updates(
        updates, [0, 1], operator="uniform_mean"
    )
    weighted = aggregate_accepted_updates(
        updates, [0, 1], operator="sample_weighted_mean", sample_counts=[1, 3]
    )

    assert np.allclose(uniform, [3.0, 5.0])
    assert np.allclose(weighted, [4.0, 6.0])
    assert uniform.dtype == updates.dtype


@pytest.mark.parametrize(
    "updates,participant_ids,update_ids",
    [
        ([], [], []),
        ([np.ones(2), np.ones(3)], [0, 1], ["r0:0", "r0:1"]),
        ([np.ones(2), np.array([1.0, np.nan])], [0, 1], ["r0:0", "r0:1"]),
        ([np.ones(2), np.ones(2)], [0, 0], ["r0:0", "r0:1"]),
        ([np.ones(2), np.ones(2)], [0, 1], ["r0:0", "r0:0"]),
        ([np.ones(2, dtype=np.float32), np.ones(2, dtype=np.float64)],
         [0, 1], ["r0:0", "r0:1"]),
    ],
)
def test_invalid_update_batches_fail_closed(updates, participant_ids, update_ids):
    with pytest.raises(ValueError):
        validate_update_batch(updates, participant_ids, update_ids=update_ids)


def test_valid_update_batch_preserves_participant_mapping():
    updates, ids, update_ids = validate_update_batch(
        [np.array([1.0, 2.0]), np.array([3.0, 4.0])],
        [9, 4],
        update_ids=["r2:9", "r2:4"],
    )
    assert updates.shape == (2, 2)
    assert ids == [9, 4]
    assert update_ids == ["r2:9", "r2:4"]


def test_ground_truth_changes_only_post_decision_metrics():
    decision = {"accepted_ids": [10, 12], "rejected_ids": [11]}
    first = evaluate_detection_decision(decision, malicious_ids={11})
    second = evaluate_detection_decision(decision, malicious_ids={10})

    assert decision == {"accepted_ids": [10, 12], "rejected_ids": [11]}
    assert (first["fpr"], first["tpr"]) != (second["fpr"], second["tpr"])


def test_server_decision_api_has_no_ground_truth_parameter():
    source = (Path(__file__).parents[1] / "simulation" / "server.py").read_text()
    signature = source.split("def aggregate(", 1)[1].split("):", 1)[0]
    assert "malicious_ids" not in signature
    assert "true_malicious" not in source


@pytest.mark.parametrize("attack_type", ["gaussian", "adaptive_gaussian"])
def test_gradient_attacks_preserve_model_update_dtype(attack_type):
    client = Client.__new__(Client)
    client.attack_type = attack_type
    client.attack_params = {"gaussian_std": 0.1, "adaptive_alpha": 0.3}
    gradient = np.array([1.0, -2.0, 3.0], dtype=np.float32)
    attacked = client._poison_gradient(gradient)
    assert attacked.dtype == gradient.dtype
    assert np.all(np.isfinite(attacked))


def test_alert_evaluator_rejects_invalid_decision_partition():
    with pytest.raises(ValueError):
        evaluate_attack_alert(
            {"accepted_ids": [1, 1], "rejected_ids": []}, {1}, False,
        )
    with pytest.raises(ValueError):
        evaluate_attack_alert(
            {"accepted_ids": [1], "rejected_ids": [1]}, {1}, False,
        )


def test_filter_indices_are_validated_before_coercion(monkeypatch):
    monkeypatch.setattr(
        server_module,
        "fed_mdbscan_g_filter",
        lambda gradients, **kwargs: ([0.5], [1], {}),
    )
    server = _server("fed_mdbscan_g")
    with pytest.raises(ValueError, match="integer indices"):
        server.aggregate(
            [np.ones(2, dtype=np.float32), np.ones(2, dtype=np.float32)],
            [0, 1], round_id=0,
        )


def test_skip_round_policy_applies_to_reason_coded_method_fallback(monkeypatch):
    monkeypatch.setattr(
        server_module,
        "fed_mdbscan_g_filter",
        lambda gradients, **kwargs: (
            [0, 1], [], {
                "fallback_applied": True,
                "fallback_reason": "cohort_below_minimum",
                "degraded": True,
            },
        ),
    )
    server = _server("fed_mdbscan_g", fallback_policy="skip_round")
    before = server.get_global_weights()
    result = server.aggregate(
        [np.ones(2, dtype=np.float32), np.ones(2, dtype=np.float32)],
        [3, 4], round_id=0,
    )
    assert result["decision"]["accepted_ids"] == []
    assert result["decision"]["rejected_ids"] == [3, 4]
    assert result["filter_info"]["fallback_reason"] == "cohort_below_minimum"
    assert np.array_equal(server.get_global_weights(), before)


def test_temporal_state_is_transactional_when_model_update_overflows(monkeypatch):
    monkeypatch.setattr(
        server_module,
        "fed_mdbscan_g_filter",
        lambda gradients, **kwargs: (
            [0], [], {
                "attack_gate": True,
                "attack_alert": True,
                "gap_concentration": 2.0,
                "layer_used": "synthetic",
            },
        ),
    )
    server = _server("fed_mdbscan_g")
    server.global_weights = np.full(2, np.finfo(np.float32).max, dtype=np.float32)
    before = server.export_defense_state()
    with pytest.raises(ValueError, match="non-finite weights"):
        server.aggregate(
            [np.full(2, np.finfo(np.float32).max, dtype=np.float32)],
            [0], update_ids=["0:0"], round_id=0,
        )
    assert server.export_defense_state() == before


def test_defense_state_checkpoint_restores_replay_guards():
    first = _server("fedavg")
    first.aggregate(
        [np.ones(2, dtype=np.float32)], [7], update_ids=["0:7"], round_id=0,
    )
    checkpoint = first.export_defense_state()
    second = _server("fedavg")
    second.restore_defense_state(checkpoint)
    assert second.export_defense_state() == checkpoint
    with pytest.raises(ValueError, match="stale"):
        second.aggregate(
            [np.ones(2, dtype=np.float32)], [7], update_ids=["0:7"], round_id=0,
        )


def test_uniform_aggregation_is_client_order_invariant():
    first = _server("fedavg")
    second = _server("fedavg")
    second.global_weights = first.get_global_weights()
    updates = [
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([3.0, 4.0], dtype=np.float32),
        np.array([-1.0, 0.0], dtype=np.float32),
    ]
    result_a = first.aggregate(updates, [10, 20, 30], round_id=0)
    result_b = second.aggregate(
        [updates[2], updates[0], updates[1]], [30, 10, 20], round_id=0,
    )
    assert set(result_a["decision"]["accepted_ids"]) == {10, 20, 30}
    assert set(result_b["decision"]["accepted_ids"]) == {10, 20, 30}
    assert np.allclose(first.get_global_weights(), second.get_global_weights())


def test_server_runtime_parameters_are_constructed_from_resolved_config():
    config = resolve_experiment_config({
        "aggregation_operator": "sample_weighted_mean",
        "fallback_policy": "skip_round",
        "method_params": {"fed_mdbscan_g": {"trust_region_factor": 3.25}},
    })
    server = Server(
        model=torch.nn.Linear(2, 1, bias=False),
        test_loader=[],
        aggregation_method="fed_mdbscan_g",
        method_params=config["method_params"]["fed_mdbscan_g"],
        aggregation_operator=config["aggregation_operator"],
        fallback_policy=config["fallback_policy"],
    )
    assert server.method_params == config["method_params"]["fed_mdbscan_g"]
    assert server.aggregation_operator == "sample_weighted_mean"
    assert server.fallback_policy == "skip_round"


def test_update_geometry_is_recorded_for_every_method_without_changing_decisions():
    """Diagnostic geometry must be observable, id-keyed, and decision-neutral."""
    updates = [
        np.array([1.0, 0.0], dtype=np.float32),
        np.array([3.0, 4.0], dtype=np.float32),
        np.array([0.0, 2.0], dtype=np.float32),
    ]
    participant_ids = [7, 8, 9]
    expected_norms = {"7": 1.0, "8": 5.0, "9": 2.0}

    for method in ("fedavg", "coord_median", "fed_mdbscan_g"):
        result = _server(method).aggregate(
            [u.copy() for u in updates], list(participant_ids), round_id=0
        )
        norms = result["update_norms"]
        assert set(norms) == {str(pid) for pid in participant_ids}
        for key, expected in expected_norms.items():
            assert norms[key] == pytest.approx(expected)
        # Accepted and rejected sets must together cover exactly the inputs,
        # so the diagnostic fields cannot have perturbed the decision.
        decision = result["decision"]
        assert sorted(decision["accepted_ids"] + decision["rejected_ids"]) == participant_ids

    # Distances to the Layer-0 geometric median exist only where a geometric
    # trust region is actually computed.
    mdbscan_result = _server("fed_mdbscan_g").aggregate(
        [u.copy() for u in updates], list(participant_ids), round_id=0
    )
    assert set(mdbscan_result["l0_distances"]) == {str(pid) for pid in participant_ids}
    assert _server("fedavg").aggregate(
        [u.copy() for u in updates], list(participant_ids), round_id=0
    )["l0_distances"] == {}


def test_update_norm_beyond_floating_point_range_is_recorded_as_null():
    """A finite update may still have an unrepresentable norm; never warn or raise."""
    huge = np.float32(1e38)
    result = _server("fedavg").aggregate(
        [np.array([huge, huge], dtype=np.float32),
         np.array([1.0, 1.0], dtype=np.float32)],
        [0, 1], round_id=0,
    )
    assert result["update_norms"]["0"] is None
    assert result["update_norms"]["1"] == pytest.approx(np.sqrt(2.0))
