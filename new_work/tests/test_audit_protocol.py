import copy
import numpy as np
import pytest
import torch
from torch.utils.data import TensorDataset, DataLoader
from simulation.contracts import build_participation_schedule, resolve_experiment_config
from simulation.data_distributor import repair_minimum_partition
from simulation.client import Client
from simulation.models import get_model_weights
from simulation.server import Server


def test_minimum_repair_preserves_union_and_is_reproducible():
    partition = {0: list(range(100)), 1: [], 2: [100], 3: list(range(101, 130))}
    repaired, moved = repair_minimum_partition(partition, 20, 7)
    assert min(map(len, repaired.values())) >= 20
    assert sorted(x for a in repaired.values() for x in a) == list(range(130))
    assert moved == 39
    assert (repaired, moved) == repair_minimum_partition(partition, 20, 7)
    with pytest.raises(ValueError):
        repair_minimum_partition({0: [1], 1: []}, 20, 7)


@pytest.mark.parametrize('active', [39, 47, 48, 100])
def test_fixed_cohort_bounds_attack_ratio_and_pairs_modes(active):
    base = dict(num_clients=100, num_rounds=30, malicious_ratio=.3, dropout_rate=.1)
    latent, rounds = build_participation_schedule(base, list(range(active)))
    assert all(set(latent) <= set(r) and len(set(r)) == int(active * .9) for r in rounds)
    assert all(len(latent) / len(r) <= .3 and len(latent) * 2 < len(r) for r in rounds)
    for mode in ('clean', 'oracle'):
        assert (latent, rounds) == build_participation_schedule({**base, 'attack_mode': mode}, list(range(active)))


@pytest.mark.parametrize('override', [{'dropout_rate': 1}, {'malicious_ratio': .5}, {'max_local_steps': 0}])
def test_invalid_regimes_fail_before_training(override):
    with pytest.raises(ValueError):
        resolve_experiment_config(override)


def test_fixed_steps_and_training_rng_are_isolated():
    data = TensorDataset(torch.ones(2, 2), torch.tensor([0, 1]))
    model_fn = lambda: torch.nn.Sequential(torch.nn.Linear(2, 5), torch.nn.Dropout(.2), torch.nn.Linear(5, 2))
    c = Client(0, DataLoader(data, batch_size=2, shuffle=True), model_fn)
    weights = get_model_weights(c.model)
    first = c.train(weights, epochs=1, max_local_steps=5, rng_seed=123)
    assert c.last_optimizer_steps == 5
    torch.rand(300)
    second = c.train(weights, epochs=1, max_local_steps=5, rng_seed=123)
    assert np.array_equal(first, second)


def test_fltrust_normalization_scales_small_updates_up(monkeypatch):
    server = Server(torch.nn.Linear(2, 1, bias=False), [], aggregation_method='fltrust_normalized')
    monkeypatch.setattr(server, '_train_root_gradient', lambda **kw: np.array([2., 0.], dtype=np.float32))
    before = server.get_global_weights()
    server.aggregate([np.array([.2, 0.], dtype=np.float32)] * 3, [0, 1, 2])
    assert np.allclose(server.get_global_weights() - before, [2., 0.])


def test_paired_end_to_end_counts_and_identity(monkeypatch):
    import simulation.run_experiment as run
    dataset = TensorDataset(torch.randn(180, 2), torch.arange(180) % 6)
    dataset.targets = torch.arange(180) % 6
    monkeypatch.setattr(run, 'load_dataset', lambda *a, **kw: (dataset, dataset))
    monkeypatch.setattr(run, 'get_model', lambda *a, **kw: torch.nn.Linear(2, 6))
    cfg = dict(dataset='har', num_clients=10, num_rounds=2, root_size=10,
               min_samples_per_client=4, non_iid_alpha=.01, malicious_ratio=.3,
               dropout_rate=.1, max_local_steps=1, attack_type='stealth_gaussian')
    results = [run.run_single_experiment({**cfg, 'attack_mode': mode}, 'fedavg', 42)
               for mode in ('attacked', 'clean', 'oracle')]
    for key in ('partition_sha256', 'initial_model_sha256', 'schedule_sha256'):
        assert len({x.run_metadata[key] for x in results}) == 1
    for index, output in enumerate(results):
        for r in output.records:
            assert r['tp']+r['fp']+r['tn']+r['fn'] == r['n_participants'] == 9
            assert r['n_malicious'] == (0 if index == 1 else 2)
            assert r['honest_majority']
            if index == 2:
                assert r['tp'] == 2 and len(r['server_input_ids']) == 7
            for d in r['attack_diagnostics'].values():
                if 'perturbation_norm' in d:
                    assert d['perturbation_norm'] / d['clean_norm'] == pytest.approx(.005, rel=1e-3)


@pytest.mark.parametrize('kind', ['minmax_omniscient', 'minsum_omniscient'])
def test_coordinated_attack_is_finite_and_inside_declared_bound(kind):
    from simulation.audit_attacks import constrained_poison
    a = np.random.default_rng(5).normal(1, .2, (30, 40)).astype(np.float32)
    poisoned, info = constrained_poison(a, kind)
    assert info['gamma'] > 0
    assert info['constraint_achieved'] <= info['constraint_bound'] * (1+1e-5)
    assert np.dot(poisoned-a.mean(0), a.mean(0)) < 0
    assert poisoned.dtype == a.dtype


def test_patch_trigger_is_normalized_and_does_not_mutate_original():
    from simulation.audit_attacks import stamp_trigger
    a = torch.zeros(2, 1, 28, 28)
    patched = stamp_trigger(a, 'mnist', 3)
    assert not a.any()
    assert torch.allclose(patched[:, :, -3:, -3:], torch.full((2, 1, 3, 3), (1-.1307)/.3081))
    assert not patched[:, :, :-3].any()


def test_flame_uses_all_update_norms_and_local_models():
    from simulation.baselines import flame_hdbscan
    a = np.random.default_rng(1).normal(size=(12, 8)).astype(np.float32)
    accepted, rejected, info = flame_hdbscan(a, np.ones(8, dtype=np.float32))
    assert info['median_norm'] == pytest.approx(np.median(np.linalg.norm(a, axis=1)))
    assert set(accepted) | set(rejected) == set(range(12))
    assert info['geometry'] == 'local_model_cosine'
