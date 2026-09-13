import json
from pathlib import Path

import pytest

from simulation.contracts import resolve_experiment_config
from simulation.run_batch_experiments import (
    BatchContractError,
    IncompleteBatchError,
    _atomic_write_json,
    _build_unit,
    _ensure_validated_output_dir,
    _read_valid_unit,
    _reduce_master,
    _reduce_scenario,
    _run_unit_path,
    _sha256_json,
)


def _config(tmp_path):
    return resolve_experiment_config({
        "num_clients": 2,
        "num_rounds": 1,
        "output_dir": str(tmp_path),
        "methods": ["fedavg"],
    })


def _records():
    return [{
        "round": 0,
        "method": "fedavg",
        "accuracy": 0.5,
        "fpr": 0.0,
        "tpr": 0.0,
        "time_elapsed": 0.01,
        "tp": 0, "fp": 0, "tn": 2, "fn": 0,
        "actual_malicious_ids": [], "n_participants": 2, "n_malicious": 0,
        "participant_ids": [0, 1],
        "update_ids": ["0:0", "0:1"],
        "accepted_ids": [0, 1],
        "rejected_ids": [],
        "fallback_applied": 0,
        "fallback_reason": "none",
        "degraded": 0,
    }]


def _metadata(config):
    digest = "a" * 64
    return {
        "dataset_identity": {
            "name": config["dataset"],
            "train": {
                "class": "Synthetic", "length": 2, "transform": "none",
                "target_transform": "none", "sha256": digest,
            },
            "test": {
                "class": "Synthetic", "length": 2, "transform": "none",
                "target_transform": "none", "sha256": "b" * 64,
            },
        },
        "partition_sha256": "c" * 64,
        "initial_model_sha256": "d" * 64,
        "model_identity": {
            "class": "SyntheticModel", "repr": "SyntheticModel()",
            "parameters": [], "sha256": "e" * 64,
        },
        "command": ["synthetic"],
        "start_time_unix": 1.0,
        "end_time_unix": 2.0,
        "peak_memory_kib": 10.0,
        "runtime": {"device": "cpu"},
        "resolved_config": config,
    }


def test_self_describing_unit_roundtrips_and_reduces_complete_batch(tmp_path):
    scenario = {"id": "synthetic", "label": "synthetic"}
    config = _config(tmp_path)
    path = _run_unit_path(str(tmp_path), "fedavg", 42)
    unit = _build_unit(
        config, scenario, "fedavg", 42, _records(), _metadata(config),
    )
    _atomic_write_json(path, unit)

    loaded = _read_valid_unit(path, "synthetic", "fedavg", 42, config)
    assert loaded["resolved_config"]["protocol_digest"] == config["protocol_digest"]
    summary = _reduce_scenario(
        str(tmp_path), {"scenario_id": "synthetic", "label": "synthetic"},
        ["fedavg"], [42], config,
    )
    assert summary["complete"] is True
    assert len(summary["unit_references"]) == 1
    assert (tmp_path / "scenario_summary.json").exists()
    csv_text = (tmp_path / "all_results.csv").read_text(encoding="utf-8")
    assert "unit_identity" in csv_text
    assert "scenario_id" in csv_text
    assert "seed" in csv_text


def test_digest_mismatch_rejects_cache(tmp_path):
    scenario = {"id": "synthetic", "label": "synthetic"}
    config = _config(tmp_path)
    path = _run_unit_path(str(tmp_path), "fedavg", 42)
    unit = _build_unit(
        config, scenario, "fedavg", 42, _records(), _metadata(config),
    )
    unit["protocol_digest"] = "wrong"
    _atomic_write_json(path, unit)

    with pytest.raises(BatchContractError, match="incompatible cached unit"):
        _read_valid_unit(path, "synthetic", "fedavg", 42, config)


def test_incomplete_or_nonfinite_batch_has_no_canonical_summary(tmp_path):
    config = _config(tmp_path)
    (tmp_path / "scenario_summary.json").write_text("stale\n", encoding="utf-8")
    (tmp_path / "all_results.csv").write_text("stale\n", encoding="utf-8")
    with pytest.raises(IncompleteBatchError):
        _reduce_scenario(
            str(tmp_path), {"scenario_id": "synthetic", "label": "synthetic"},
            ["fedavg"], [42], config,
        )
    assert not (tmp_path / "scenario_summary.json").exists()
    assert not (tmp_path / "all_results.csv").exists()
    assert (tmp_path / "scenario_progress.json").exists()

    scenario = {"id": "synthetic", "label": "synthetic"}
    path = _run_unit_path(str(tmp_path), "fedavg", 42)
    records = _records()
    records[0]["accuracy"] = float("nan")
    with pytest.raises(BatchContractError, match="non-finite"):
        _build_unit(
            config, scenario, "fedavg", 42, records, _metadata(config),
        )


@pytest.mark.parametrize(
    "methods,seeds",
    [([], [42]), (["fedavg"], []), (["fedavg", "fedavg"], [42]),
     (["fedavg"], [42, 42])],
)
def test_empty_or_duplicate_matrix_dimensions_fail_closed(tmp_path, methods, seeds):
    with pytest.raises(BatchContractError):
        _reduce_scenario(
            str(tmp_path), {"scenario_id": "synthetic", "label": "synthetic"},
            methods, seeds, _config(tmp_path),
        )


@pytest.mark.parametrize(
    "key,value",
    [("accuracy", 1.1), ("fpr", -0.1), ("tpr", 2.0), ("time_elapsed", -1.0)],
)
def test_impossible_scientific_record_values_are_rejected(tmp_path, key, value):
    config = _config(tmp_path)
    records = _records()
    records[0][key] = value
    with pytest.raises(BatchContractError):
        _build_unit(
            config, {"id": "synthetic"}, "fedavg", 42, records,
            _metadata(config),
        )


def test_missing_run_provenance_is_rejected(tmp_path):
    config = _config(tmp_path)
    with pytest.raises(BatchContractError, match="run_metadata"):
        _build_unit(config, {"id": "synthetic"}, "fedavg", 42, _records())


def test_master_rejects_foreign_or_stale_scenario_summary(tmp_path):
    config = _config(tmp_path)
    scenario = {
        "id": "synthetic", "label": "synthetic", "alpha": 0.5,
        "malicious_ratio": 0.0, "attack_type": "gaussian",
    }
    unit_path = _run_unit_path(str(tmp_path / "scenario_synthetic"), "fedavg", 42)
    unit = _build_unit(
        config, scenario, "fedavg", 42, _records(), _metadata(config),
    )
    _atomic_write_json(unit_path, unit)
    scenario_dir = tmp_path / "scenario_synthetic"
    _reduce_scenario(
        str(scenario_dir), {
            "scenario_id": "synthetic",
            "label": "synthetic",
            "dataset": config["dataset"],
            "alpha": scenario["alpha"],
            "malicious_ratio": scenario["malicious_ratio"],
            "attack_type": scenario["attack_type"],
            "num_clients": config["num_clients"],
            "num_rounds": config["num_rounds"],
            "dropout_rate": config["dropout_rate"],
            "data_size_sigma": config["data_size_sigma"],
        },
        ["fedavg"], [42], config,
    )
    contract = {**config, "scenario": scenario, "seeds": [42]}
    contract["scenario_fingerprint"] = _sha256_json(contract)
    _atomic_write_json(str(scenario_dir / "scenario_config.json"), contract)
    summaries = _reduce_master(str(tmp_path), [scenario])
    assert len(summaries) == 1

    summary_path = scenario_dir / "scenario_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["scenario_id"] = "foreign"
    _atomic_write_json(str(summary_path), summary)
    with pytest.raises(IncompleteBatchError):
        _reduce_master(str(tmp_path), [scenario])
    assert not (tmp_path / "master_summary.json").exists()


def test_validated_batch_cannot_target_a_legacy_result_root():
    project_root = Path(__file__).resolve().parents[2]
    legacy = project_root / "new_work/results/heterogeneous_v3_mnist"
    with pytest.raises(BatchContractError, match="legacy"):
        _ensure_validated_output_dir(legacy)
