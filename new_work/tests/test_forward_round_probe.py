import json

import numpy as np
import pytest

from simulation.contracts import derive_seed
from simulation.forward_round_probe import (
    ROUND_SEED_PURPOSES, STATE_VERSION, run_reference)
from simulation.server import Server


def _round_seed_shim(checkpoint_round):
    """The remapping run_branch installs, isolated so it can be tested alone."""
    def derive(seed, *parts):
        if len(parts) >= 2 and parts[0] in ROUND_SEED_PURPOSES and parts[1] == 0:
            parts = (parts[0], checkpoint_round) + tuple(parts[2:])
        return derive_seed(seed, *parts)
    return derive


def test_branch_round_zero_reproduces_the_reference_round_streams():
    derive = _round_seed_shim(9)
    for purpose in ROUND_SEED_PURPOSES:
        assert derive(42, purpose, 0, 7) == derive_seed(42, purpose, 9, 7)
    # A purpose that carries no round index must pass through untouched.
    assert derive(42, 'batch_probe', 0) == derive_seed(42, 'batch_probe', 0)
    assert derive(42, 'partition_repair') == derive_seed(42, 'partition_repair')


def test_round_seed_shim_only_rewrites_the_branch_round():
    derive = _round_seed_shim(19)
    # Round indices other than the branch's own round 0 are never rewritten.
    assert derive(42, 'client_training', 3, 1) == derive_seed(42, 'client_training', 3, 1)
    assert derive(42, 'client_training', 0, 1) != derive_seed(42, 'client_training', 0, 1)


def test_reference_rejects_checkpoints_outside_the_horizon():
    config = {'num_rounds': 5, 'seed': 42}
    with pytest.raises(ValueError):
        run_reference(config, [5], None)
    with pytest.raises(ValueError):
        run_reference(config, [-1], None)


def test_captured_defense_state_round_trips_without_replay_counters(tmp_path):
    """A branch restores decision memory but starts its own replay bookkeeping."""
    model = __import__('torch').nn.Linear(2, 1, bias=False)
    server = Server(model=model, test_loader=[], aggregation_method='fed_mdbscan_g')
    server.detected_attack_history = [True, False]
    server.attack_alert_log = [True, True]
    server.gap_concentration_log = [11.0, 3.0]
    server.layer_used_log = ['L0_only', 'L0_only']
    server.clean_round_streak = 1
    server._seen_update_ids = {'8:1'}
    server._last_round_id = 8

    state = server.export_defense_state()
    branch_state = dict(state, last_round_id=None, seen_update_ids=[])
    json.loads(json.dumps(branch_state))  # must survive the checkpoint file

    fresh = Server(model=__import__('torch').nn.Linear(2, 1, bias=False),
                   test_loader=[], aggregation_method='fed_mdbscan_g')
    fresh.restore_defense_state(branch_state)
    assert fresh.detected_attack_history == [True, False]
    assert fresh.clean_round_streak == 1
    assert fresh.gap_concentration_log == [11.0, 3.0]
    # Cleared, so a branch may aggregate as round 0 after a round-8 checkpoint.
    assert fresh._last_round_id is None
    assert fresh._seen_update_ids == set()
    fresh.aggregate([np.ones(2, dtype=np.float32), np.ones(2, dtype=np.float32),
                     np.ones(2, dtype=np.float32)], [0, 1, 2], round_id=0)


def test_state_version_is_pinned():
    assert STATE_VERSION == 'fed-mdbscan-g-forward-round-v1'
