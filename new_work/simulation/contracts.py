"""Executable scientific contracts for validated Fed-MDBSCAN-G runs.

The legacy simulation accepted partially-specified dictionaries and filled several
scientific parameters at their call sites.  This module is the single place where
those defaults are resolved, validated, serialized, and hashed for G0--G1.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np


SCHEMA_VERSION = "fed-mdbscan-g-unit-v2"
PROTOCOL_VERSION = "audit-contract-v2"
VALIDATED_RUN_NAMESPACE = "validated/audit-v2"


_MDBSCAN_G_BASE_PARAMS = {
    "k": 5,
    "t": "auto",
    "eps": "auto",
    "min_pts": 3,
    "consensus_threshold": 2.0,
    "trust_region_factor": 2.5,
    "gap_concentration_threshold": 10.0,
    "min_attack_gate_l0_ratio": 0.05,
    "min_attack_gate_l0_count": 2,
    "safety_valve_ratio": 0.5,
    "momentum_window": 3,
    "enable_l2": True,
    "enable_momentum": True,
    "enable_safety_valve": True,
    "enable_snnc_cutoff": True,
}

# Layer-ablation and trust-region-sweep variants of the proposed method.
# Each variant inherits every published hyperparameter and differs in exactly
# one dimension, so an accuracy or FPR delta is attributable to that single
# dimension. `fed_g2l_25` is the matching control: FedG2L is the same
# geometric-median distance filter as Layer 0, so running it at the same
# radius isolates how much of the reported margin comes from the radius
# rather than from the multi-density machinery.
MDBSCAN_ABLATION_VARIANTS = {
    "mdbg_no_snnc_cutoff": {"enable_snnc_cutoff": False},
    "mdbg_l0_only":     {"enable_l2": False},
    "mdbg_no_momentum": {"enable_momentum": False},
    "mdbg_no_valve":    {"enable_safety_valve": False},
    "mdbg_rtr15":       {"trust_region_factor": 1.5},
    "mdbg_rtr20":       {"trust_region_factor": 2.0},
    "mdbg_rtr30":       {"trust_region_factor": 3.0},
}
MDBSCAN_FAMILY_METHODS = ("fed_mdbscan_g", *MDBSCAN_ABLATION_VARIANTS)


DEFAULT_EXPERIMENT_CONFIG = {
    "schema_version": SCHEMA_VERSION,
    "protocol_version": PROTOCOL_VERSION,
    "validated_run_namespace": VALIDATED_RUN_NAMESPACE,
    "dataset": "mnist",
    "num_classes": None,
    "num_clients": 20,
    "num_rounds": 20,
    "local_epochs": 3,
    "lr": 0.01,
    "optimizer_momentum": 0.9,
    "batch_size": 32,
    "test_batch_size": 128,
    "root_batch_size": 32,
    "malicious_ratio": 0.0,
    "attack_type": "gaussian",
    "gaussian_std": 5.0,
    "stealth_rho": 0.005,
    "stealth_rho_sensitivity": [0.001, 0.01],
    "adaptive_alpha": 0.3,
    "coordinated_profile_ratio": 1.0,
    "backdoor_fraction": 0.2,
    "backdoor_target": 0,
    "backdoor_patch_size": 3,
    "non_iid_alpha": 0.5,
    "iid": False,
    "data_size_sigma": 0.0,
    "min_samples_per_client": 20,
    "empty_client_policy": "preserve_empty",
    "partition_policy": "repair_minimum",
    "attack_mode": "attacked",
    "attack_start_round": 0,
    "attack_end_round": None,
    "max_local_steps": None,
    "rng_policy": "purpose-seed-v2",
    "participation_policy": "fixed_round_size",
    "dropout_rate": 0.0,
    "malicious_participation_policy": "always_participate",
    "aggregation_operator": "uniform_mean",
    "fallback_policy": "accept_all_degraded",
    "seed": 42,
    "data_dir": "./data",
    "output_dir": "./results/validated/audit-v2/single",
    "root_size": 100,
    "methods": ["fed_mdbscan_g", "fed_dbscan", "fed_rra", "fed_g2l"],
    "method_params": {
        "fed_mdbscan_g": dict(_MDBSCAN_G_BASE_PARAMS),
        **{
            name: {**_MDBSCAN_G_BASE_PARAMS, **overrides}
            for name, overrides in MDBSCAN_ABLATION_VARIANTS.items()
        },
        "fed_dbscan": {"eps": "auto", "min_pts": 3},
        "fed_rra": {
            "eps": "auto",
            "min_pts": 3,
            "reputation_threshold": 0.5,
        },
        "fed_g2l": {"threshold_factor": 1.5},
        "fed_g2l_25": {"threshold_factor": 2.5},
        "krum": {"num_malicious": None, "multi_krum_m": None},
        "krum_bound30": {"max_attack_ratio": 0.3, "multi_krum_m": None},
        "coord_median": {},
        "fltrust": {
            "root_lr": 0.01,
            "root_epochs": 1,
            "root_momentum": 0.9,
            "clip_to_root_norm": True,
        },
        "flame": {"noise_std": 0.001, "eps_dbscan": "auto"},
        "flame_hdbscan": {"noise_std": 0.001},
        "fltrust_normalized": {"root_lr": 0.01, "root_epochs": 3, "root_momentum": 0.9, "clip_to_root_norm": True},
        "fedavg": {},
        "sample_weighted_mean": {},
        "norm_clip": {"threshold_factor": 2.5},
    },
}


SUPPORTED_DATASETS = {"mnist", "fashion_mnist", "har", "cifar10"}
SUPPORTED_ATTACKS = {
    "gaussian", "label_flip", "stealth_gaussian", "adaptive_gaussian",
    "scale", "sign_flip", "minmax_omniscient", "minsum_omniscient", "patch_backdoor",
    "minmax_flat_omniscient",
}


def _merge_dict(base: dict[str, Any], override: Mapping[str, Any],
                path: str = "config") -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if not isinstance(key, str):
            raise TypeError(f"{path} keys must be strings")
        if path == "config" and key == "protocol_digest":
            continue
        if key not in merged:
            raise ValueError(f"unknown configuration key: {path}.{key}")
        if isinstance(value, Mapping) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value, f"{path}.{key}")
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _json_value(value: Any) -> Any:
    """Convert supported config values to a deterministic JSON value."""
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JSON mapping keys must be strings")
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"configuration value is not JSON-serializable: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Return the canonical UTF-8 JSON representation used for digests."""
    return json.dumps(
        _json_value(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )


def protocol_digest(config: Mapping[str, Any]) -> str:
    """Hash a resolved protocol, excluding run identity and mutable paths."""
    scientific = {
        key: value
        for key, value in config.items()
        if key not in {
            "protocol_digest", "seed", "output_dir", "data_dir",
        }
    }
    return hashlib.sha256(canonical_json(scientific).encode("utf-8")).hexdigest()


def _finite_number(name: str, value: Any, *, minimum: float | None = None,
                   maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        raise TypeError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return result


def resolve_experiment_config(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Resolve every effective G0--G1 experiment parameter and attach its digest."""
    if config is not None and not isinstance(config, Mapping):
        raise TypeError("config must be a mapping")
    resolved = _merge_dict(DEFAULT_EXPERIMENT_CONFIG, config or {})

    identities = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "validated_run_namespace": VALIDATED_RUN_NAMESPACE,
    }
    for name, expected in identities.items():
        if resolved[name] != expected:
            raise ValueError(f"{name} is immutable and must equal {expected!r}")

    if resolved["dataset"] not in SUPPORTED_DATASETS:
        raise ValueError(f"unsupported dataset: {resolved['dataset']}")
    expected_classes = 6 if resolved["dataset"] == "har" else 10
    if resolved["num_classes"] is None:
        resolved["num_classes"] = expected_classes
    if (isinstance(resolved["num_classes"], bool)
            or not isinstance(resolved["num_classes"], int)
            or resolved["num_classes"] <= 1):
        raise ValueError("num_classes must be an integer greater than one")
    if resolved["num_classes"] != expected_classes:
        raise ValueError("num_classes does not match the selected dataset")

    for name in (
        "num_clients", "num_rounds", "local_epochs", "batch_size",
        "test_batch_size", "root_batch_size",
    ):
        value = resolved[name]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    seed = resolved["seed"]
    if (isinstance(seed, bool) or not isinstance(seed, int)
            or seed < 0 or seed > 2**32 - 1):
        raise ValueError("seed must be an integer in [0, 2**32-1]")
    min_samples = resolved["min_samples_per_client"]
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 0:
        raise ValueError("min_samples_per_client must be a non-negative integer")
    root_size = resolved["root_size"]
    if isinstance(root_size, bool) or not isinstance(root_size, int) or root_size < 0:
        raise ValueError("root_size must be a non-negative integer")
    if not isinstance(resolved["stealth_rho_sensitivity"], list):
        raise TypeError("stealth_rho_sensitivity must be a list")

    _finite_number("lr", resolved["lr"], minimum=0.0)
    _finite_number("optimizer_momentum", resolved["optimizer_momentum"],
                   minimum=0.0, maximum=1.0)
    _finite_number("malicious_ratio", resolved["malicious_ratio"], minimum=0.0, maximum=1.0)
    if resolved["malicious_ratio"] >= 0.5:
        raise ValueError("malicious_ratio must be less than 0.5")
    alpha = _finite_number("non_iid_alpha", resolved["non_iid_alpha"], minimum=0.0)
    if not resolved["iid"] and alpha <= 0.0:
        raise ValueError("non_iid_alpha must be positive when iid is false")
    _finite_number("data_size_sigma", resolved["data_size_sigma"], minimum=0.0)
    _finite_number("dropout_rate", resolved["dropout_rate"], minimum=0.0, maximum=1.0)
    _finite_number("stealth_rho", resolved["stealth_rho"], minimum=0.0)
    _finite_number("gaussian_std", resolved["gaussian_std"], minimum=0.0)
    _finite_number("adaptive_alpha", resolved["adaptive_alpha"], minimum=0.0)
    for rho in resolved["stealth_rho_sensitivity"]:
        _finite_number("stealth_rho_sensitivity", rho, minimum=0.0)

    if not isinstance(resolved["iid"], bool):
        raise TypeError("iid must be a boolean")
    _finite_number("backdoor_fraction", resolved["backdoor_fraction"], minimum=0, maximum=1)
    for name in ('backdoor_target', 'backdoor_patch_size'):
        value = resolved[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < (1 if name.endswith('size') else 0):
            raise ValueError(f'invalid {name}')
    if resolved['backdoor_target'] >= expected_classes or resolved['backdoor_patch_size'] > 28:
        raise ValueError('invalid backdoor target or patch size')
    if resolved['attack_type'] == 'patch_backdoor' and resolved['dataset'] == 'har':
        raise ValueError('image patch backdoor is not defined for HAR')
    if resolved["attack_type"] not in SUPPORTED_ATTACKS:
        raise ValueError(f"unsupported attack_type: {resolved['attack_type']}")
    _finite_number("coordinated_profile_ratio", resolved["coordinated_profile_ratio"],
                   minimum=0.0)
    methods = resolved["methods"]
    if (not isinstance(methods, list) or not methods
            or any(not isinstance(method, str) for method in methods)
            or len(set(methods)) != len(methods)):
        raise ValueError("methods must be a non-empty list of unique strings")
    unknown_methods = set(methods) - set(resolved["method_params"])
    if unknown_methods:
        raise ValueError(f"unsupported methods: {sorted(unknown_methods)}")

    if resolved["empty_client_policy"] != "preserve_empty":
        raise ValueError("empty_client_policy must be 'preserve_empty'")
    if resolved["malicious_participation_policy"] != "always_participate":
        raise ValueError("only always_participate is supported in the validated protocol")
    if resolved["aggregation_operator"] not in {"uniform_mean", "sample_weighted_mean"}:
        raise ValueError("unsupported aggregation_operator")
    if resolved["fallback_policy"] not in {"accept_all_degraded", "skip_round"}:
        raise ValueError("unsupported fallback_policy")
    if (not isinstance(resolved["data_dir"], str) or not resolved["data_dir"]
            or not isinstance(resolved["output_dir"], str) or not resolved["output_dir"]):
        raise ValueError("data_dir and output_dir must be non-empty strings")

    if resolved["partition_policy"] not in {"repair_minimum", "preserve_empty"}:
        raise ValueError("unsupported partition_policy")
    if resolved["partition_policy"] == "repair_minimum" and min_samples < 1:
        raise ValueError("repair_minimum requires a positive min_samples_per_client")
    if resolved["attack_mode"] not in {"attacked", "clean", "oracle"}:
        raise ValueError("unsupported attack_mode")
    for name in ("attack_start_round", "attack_end_round", "max_local_steps"):
        value = resolved[name]
        if value is None and name != "attack_start_round":
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < (1 if name == "max_local_steps" else 0):
            raise ValueError(f"invalid {name}")
    if resolved["attack_end_round"] is not None and resolved["attack_end_round"] <= resolved["attack_start_round"]:
        raise ValueError("attack_end_round must exceed attack_start_round (exclusive end)")
    if resolved["participation_policy"] != "fixed_round_size" or resolved["rng_policy"] != "purpose-seed-v2":
        raise ValueError("unsupported participation or RNG policy")
    if resolved["dropout_rate"] >= 1:
        raise ValueError("dropout_rate must leave participants")
    _finite_number("norm_clip.threshold_factor", resolved["method_params"]["norm_clip"]["threshold_factor"], minimum=0)

    # The proposed method and every ablation variant share one schema, so
    # they are validated under the same rules; a mistyped ablation override
    # fails here rather than silently producing an uninterpretable run.
    for family_method in MDBSCAN_FAMILY_METHODS:
        fed_g = resolved["method_params"][family_method]
        prefix = f"method_params.{family_method}"
        for name in ("k", "min_pts", "min_attack_gate_l0_count", "momentum_window"):
            value = fed_g[name]
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{prefix}.{name} must be positive")
        for name, minimum, maximum in (
            ("consensus_threshold", 0.0, None),
            ("trust_region_factor", 0.0, None),
            ("gap_concentration_threshold", 0.0, None),
            ("min_attack_gate_l0_ratio", 0.0, 1.0),
            ("safety_valve_ratio", 0.0, 1.0),
        ):
            _finite_number(
                f"{prefix}.{name}", fed_g[name],
                minimum=minimum, maximum=maximum,
            )
        for name in ("t", "eps"):
            value = fed_g[name]
            if value != "auto":
                _finite_number(f"{prefix}.{name}", value, minimum=0.0)
        for name in ("enable_l2", "enable_momentum", "enable_safety_valve", "enable_snnc_cutoff"):
            if not isinstance(fed_g[name], bool):
                raise ValueError(f"{prefix}.{name} must be a boolean")
    for m in ("flame", "flame_hdbscan"):
        _finite_number(f"{m}.noise_std", resolved["method_params"][m]["noise_std"], minimum=0)
    _finite_number("krum_bound30.max_attack_ratio", resolved["method_params"]["krum_bound30"]["max_attack_ratio"], minimum=0, maximum=0.49)
    for fltrust_method in ("fltrust", "fltrust_normalized"):
        fltrust = resolved["method_params"][fltrust_method]
        if (isinstance(fltrust["root_epochs"], bool)
                or not isinstance(fltrust["root_epochs"], int)
                or fltrust["root_epochs"] <= 0):
            raise ValueError("method_params.fltrust.root_epochs must be positive")
        _finite_number("method_params.fltrust.root_lr", fltrust["root_lr"], minimum=0.0)
        _finite_number(
            "method_params.fltrust.root_momentum", fltrust["root_momentum"],
            minimum=0.0, maximum=1.0,
        )
        if not isinstance(fltrust["clip_to_root_norm"], bool):
            raise TypeError("method_params.fltrust.clip_to_root_norm must be boolean")

    resolved = _json_value(resolved)
    resolved["protocol_digest"] = protocol_digest(resolved)
    return resolved


def derive_seed(seed, *parts):
    """Stable independent random streams, unaffected by execution order."""
    payload = canonical_json([int(seed), *parts]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "little")


def build_participation_schedule(config, active_client_ids):
    resolved = resolve_experiment_config(config)
    active = sorted(active_client_ids)
    if len(set(active)) != len(active) or not active:
        raise ValueError("active client IDs must be non-empty and unique")
    round_size = math.floor(len(active) * (1.0 - resolved["dropout_rate"]))
    if round_size < 1:
        raise ValueError("fixed round cohort is empty")
    malicious_count = math.floor(round_size * resolved["malicious_ratio"])
    if resolved["malicious_ratio"] > 0 and malicious_count == 0:
        raise ValueError("positive attack ratio rounds to zero attackers")
    rng = np.random.default_rng(derive_seed(resolved["seed"], "attacker_assignment"))
    malicious = sorted(int(i) for i in rng.choice(active, malicious_count, replace=False))
    benign = [i for i in active if i not in set(malicious)]
    schedule = []
    for round_id in range(resolved["num_rounds"]):
        rng = np.random.default_rng(derive_seed(resolved["seed"], "participation", round_id))
        chosen = rng.choice(benign, round_size - malicious_count, replace=False)
        schedule.append(sorted(malicious + [int(i) for i in chosen]))
    return malicious, schedule


def expected_participation(config, active_count=None):
    resolved = resolve_experiment_config(config)
    active = resolved["num_clients"] if active_count is None else active_count
    total = math.floor(active * (1.0 - resolved["dropout_rate"]))
    malicious = math.floor(total * resolved["malicious_ratio"])
    return {"active_clients": active, "malicious_clients": malicious,
            "benign_clients": active - malicious,
            "expected_benign_participants": total - malicious,
            "expected_total_participants": total,
            "malicious_participation_policy": "always_participate"}


def stealth_gaussian_perturbation(gradient: np.ndarray, rho: float = 0.005,
                                  rng: Any | None = None) -> np.ndarray:
    """Add a random-direction perturbation with exact total norm ``rho*||g||``."""
    array = np.asarray(gradient)
    if array.size == 0 or array.dtype.kind != "f":
        raise ValueError("gradient must be a non-empty real floating-point array")
    if not np.all(np.isfinite(array)):
        raise ValueError("gradient must contain only finite values")
    rho_value = _finite_number("rho", rho, minimum=0.0)
    work = array.astype(np.float64, copy=False)
    scale = float(np.max(np.abs(work)))
    norm = 0.0 if scale == 0.0 else scale * float(np.linalg.norm(work / scale))
    if not math.isfinite(norm):
        raise ValueError("gradient norm is not finite")
    if norm == 0.0 or rho_value == 0.0:
        return array.copy()

    generator = np.random if rng is None else rng
    direction = np.asarray(generator.normal(0.0, 1.0, size=array.shape), dtype=np.float64)
    direction_norm = float(np.linalg.norm(direction))
    if not math.isfinite(direction_norm) or direction_norm == 0.0:
        raise ValueError("random direction must have a finite non-zero norm")
    target_norm = rho_value * norm
    if not math.isfinite(target_norm):
        raise ValueError("perturbation norm overflowed")
    perturbation = direction * (target_norm / direction_norm)
    result = work + perturbation
    if not np.all(np.isfinite(perturbation)) or not np.all(np.isfinite(result)):
        raise ValueError("perturbation produced a non-finite update")
    cast = result.astype(array.dtype, copy=False)
    if not np.all(np.isfinite(cast)):
        raise ValueError("perturbation overflowed the gradient dtype")
    return cast


def apply_lognormal_retention(client_indices: Mapping[Any, list[int]], sigma: float = 0.5,
                              min_samples: int = 20, seed: int = 42,
                              empty_client_policy: str = "preserve_empty") -> dict[Any, list[int]]:
    """Apply post-partition lognormal retention without manufacturing samples."""
    if not isinstance(client_indices, Mapping):
        raise TypeError("client_indices must be a mapping")
    sigma_value = _finite_number("sigma", sigma, minimum=0.0)
    if isinstance(min_samples, bool) or not isinstance(min_samples, int):
        raise TypeError("min_samples must be an integer")
    if min_samples < 0:
        raise ValueError("min_samples must be non-negative")
    if empty_client_policy != "preserve_empty":
        raise ValueError("empty_client_policy must be 'preserve_empty'")

    if (isinstance(seed, bool) or not isinstance(seed, int)
            or seed < 0 or seed > 2**32 - 1):
        raise ValueError("seed must be an integer in [0, 2**32-1]")
    rng = np.random.default_rng(seed)
    retained: dict[Any, list[int]] = {}
    ordered = sorted(client_indices.items(), key=lambda item: canonical_json(item[0]))
    for client_id, values in ordered:
        indices = list(values)
        if not indices:
            retained[client_id] = []
            continue
        multiplier = min(float(rng.lognormal(mean=0.0, sigma=sigma_value)), 1.0)
        target = min(len(indices), max(min_samples, int(round(len(indices) * multiplier))))
        if target == len(indices):
            retained[client_id] = indices
        else:
            retained[client_id] = rng.choice(indices, size=target, replace=False).tolist()
    return retained


def validate_update_batch(updates: Any, participant_ids: Any,
                          update_ids: Any | None = None) -> tuple[np.ndarray, list[Any], list[Any]]:
    """Validate a server-visible update batch before any geometric operation."""
    if not isinstance(updates, (list, tuple, np.ndarray)) or len(updates) == 0:
        raise ValueError("update batch must be non-empty")
    if not isinstance(participant_ids, (list, tuple)) or len(participant_ids) != len(updates):
        raise ValueError("participant_ids must map one-to-one to updates")
    participants = list(participant_ids)
    if any(isinstance(item, bool) or (
            isinstance(item, (float, np.floating)) and not np.isfinite(item)
    ) for item in participants):
        raise ValueError("participant IDs must be finite, non-boolean values")
    try:
        unique_participants = set(participants)
    except TypeError as exc:
        raise ValueError("participant IDs must be hashable") from exc
    if len(unique_participants) != len(participants):
        raise ValueError("participant IDs must be unique within a round")

    arrays = [np.asarray(update) for update in updates]
    reference_shape = arrays[0].shape
    reference_dtype = arrays[0].dtype
    if arrays[0].size == 0 or arrays[0].dtype.kind != "f":
        raise ValueError("updates must be non-empty real floating-point arrays")
    for array in arrays:
        if array.shape != reference_shape:
            raise ValueError("all updates must have identical shapes")
        if array.dtype != reference_dtype:
            raise ValueError("all updates must have identical dtypes")
        if array.dtype.kind != "f" or not np.all(np.isfinite(array)):
            raise ValueError("all updates must be finite real floating-point arrays")

    if update_ids is None:
        identities = [None] * len(arrays)
    else:
        if not isinstance(update_ids, (list, tuple)) or len(update_ids) != len(arrays):
            raise ValueError("update_ids must map one-to-one to updates")
        identities = list(update_ids)
        if any(isinstance(item, bool) or (
                isinstance(item, (float, np.floating)) and not np.isfinite(item)
        ) for item in identities):
            raise ValueError("update IDs must be finite, non-boolean values")
        try:
            if len(set(identities)) != len(identities):
                raise ValueError("update IDs must be unique within a round")
        except TypeError as exc:
            raise ValueError("update IDs must be hashable") from exc
    return np.stack(arrays, axis=0), participants, identities


def aggregate_accepted_updates(updates: np.ndarray, accepted_indices: Any,
                               operator: str = "uniform_mean",
                               sample_counts: Any | None = None) -> np.ndarray:
    """Apply an explicitly named aggregation operator to accepted updates."""
    array = np.asarray(updates)
    accepted = list(accepted_indices)
    if array.ndim < 2 or array.dtype.kind != "f" or not accepted:
        raise ValueError("at least one accepted update is required")
    if any(isinstance(i, bool) or not isinstance(i, (int, np.integer))
           or i < 0 or i >= len(array) for i in accepted):
        raise ValueError("accepted index is outside the update batch")
    if len(set(accepted)) != len(accepted):
        raise ValueError("accepted_indices must be unique")
    selected = array[accepted]
    if not np.all(np.isfinite(selected)):
        raise ValueError("accepted updates must be finite")

    if operator == "uniform_mean":
        result = np.mean(selected, axis=0, dtype=np.float64)
    elif operator == "sample_weighted_mean":
        if sample_counts is None or len(sample_counts) != len(array):
            raise ValueError("sample_weighted_mean requires one sample count per update")
        weights = np.asarray(sample_counts, dtype=np.float64)
        if not np.all(np.isfinite(weights)) or np.any(weights < 0):
            raise ValueError("sample counts must be non-negative finite values")
        accepted_weights = weights[accepted]
        if float(np.sum(accepted_weights)) <= 0.0:
            raise ValueError("accepted sample counts must have positive total weight")
        result = np.average(
            selected.astype(np.float64), axis=0, weights=accepted_weights,
        )
    else:
        raise ValueError(f"unsupported aggregation operator: {operator}")
    if not np.all(np.isfinite(result)):
        raise ValueError("aggregation produced a non-finite update")
    cast = np.asarray(result, dtype=array.dtype)
    if not np.all(np.isfinite(cast)):
        raise ValueError("aggregation overflowed the update dtype")
    return cast
