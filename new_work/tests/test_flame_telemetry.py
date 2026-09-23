"""Distinguish cluster output, skipped fits and server fallback in saved records."""
import json

import numpy as np
import pytest
import torch
from sklearn.cluster import HDBSCAN

from simulation.baselines import flame_hdbscan
from simulation.server import Server


@pytest.mark.parametrize('fallback_policy', ['accept_all_degraded', 'skip_round'])
def test_empty_cluster_telemetry_survives_server_fallback(monkeypatch, fallback_policy):
    monkeypatch.setattr(HDBSCAN, 'fit_predict', lambda self, x: np.full(len(x), -1))
    server = Server(torch.nn.Linear(2, 1, bias=False), [],
                    aggregation_method='flame_hdbscan', fallback_policy=fallback_policy)
    result = server.aggregate(
        [np.array(x, dtype=np.float32) for x in [[1,0], [0,1], [-1,0], [0,-1], [2,1]]],
        [10,20,30,40,50], round_id=0)
    telemetry = result['filter_info']['flame_clustering']
    assert telemetry['executed']
    assert telemetry['cluster_sizes'] == {}
    assert telemetry['noise_count'] == 5
    assert telemetry['selected_count_before_fallback'] == 0
    assert len(result['decision']['accepted_ids']) == (5 if fallback_policy=='accept_all_degraded' else 0)
    assert json.loads(json.dumps(telemetry)) == telemetry


@pytest.mark.parametrize('updates,reason', [
    ([[1,0],[0,1]], 'small_cohort'),
    ([[0,0]]*7, 'zero_distances'),
])
def test_skipped_fit_does_not_invent_cluster_sizes(monkeypatch, updates, reason):
    def forbidden(*args, **kwargs):
        raise AssertionError('HDBSCAN must not run for this branch')
    monkeypatch.setattr(HDBSCAN, 'fit_predict', forbidden)
    # Axis-aligned reference gives exactly zero cosine distance; [1,2] can
    # produce a nonzero 1e-16 rounding residual and correctly execute HDBSCAN.
    accepted, _, info = flame_hdbscan(np.array(updates, dtype=np.float32), np.array([1,0],dtype=np.float32))
    t = info['flame_clustering']
    assert not t['executed']
    assert t['skip_reason'] == reason
    assert t['cluster_sizes'] is None and t['noise_count'] is None
    assert t['selected_count_before_fallback'] == len(accepted) == len(updates)


def test_cluster_labels_reach_saved_round_records(monkeypatch):
    import simulation.run_experiment as run
    generator = torch.Generator().manual_seed(77)
    dataset = torch.utils.data.TensorDataset(torch.randn(180,2,generator=generator), torch.arange(180)%6)
    dataset.targets = torch.arange(180)%6
    monkeypatch.setattr(run, 'load_dataset', lambda *a, **kw: (dataset,dataset))
    monkeypatch.setattr(run, 'get_model', lambda *a, **kw: torch.nn.Linear(2,6))
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: False)
    # Nonzero label avoids relying on a particular HDBSCAN label number.
    labels = np.array([7]*5+[-1]*4)
    monkeypatch.setattr(HDBSCAN, 'fit_predict', lambda self,x: labels.copy())
    config = dict(dataset='har', num_clients=10, num_rounds=1, root_size=10,
                  min_samples_per_client=4, non_iid_alpha=.1, malicious_ratio=0,
                  dropout_rate=.1, max_local_steps=1, attack_mode='clean')
    metrics = run.run_single_experiment(config,'flame_hdbscan',42)
    record = metrics.records[0]
    t = record['flame_clustering']
    assert t['executed'] and t['skip_reason']=='none'
    assert t['cluster_sizes'] == {'7':5}
    assert t['noise_count']==4
    assert t['selected_count_before_fallback']==len(record['accepted_ids'])==5
    assert not record['fallback_applied']
    assert json.loads(json.dumps(record))['flame_clustering']==t
