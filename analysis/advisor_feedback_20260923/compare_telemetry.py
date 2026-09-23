"""Compare frozen/current FLAME selectors through the same live server.

These are bounded synthetic checks, not a replay of the training campaign or
a comparison to the FLAME authors' implementation.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root/'new_work'))
    import simulation.server as server_module
    from simulation.baselines import flame_hdbscan
    frozen_path = root/'new_work/results/validated/audit-v2/full_20260910/source/new_work/simulation/baselines.py'
    spec = importlib.util.spec_from_file_location('frozen_baselines', frozen_path)
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    base = [[.1,0],[.12,.01],[.08,-.01],[.11,.02],[.09,-.02],[-8,9],[-9,8]]
    cases = [
        ('majority', base, [0,0], False),
        ('nonzero_global', base, [1,2], False),
        ('identical', [[.1,0]]*7, [0,0], False),
        ('two_clients', [[1,0],[-2,0]], [0,0], False),
        ('zero_updates', [[0,0]]*7, [1,0], False),
        ('forced_no_majority', base, [0,0], True),
    ]
    comparisons = []
    for name, updates, weights, force_empty in cases:
        u = np.asarray(updates, dtype=np.float32)
        w = np.asarray(weights, dtype=np.float32)

        def run(selector):
            model = torch.nn.Linear(len(w), 1, bias=False)
            with torch.no_grad():
                model.weight.copy_(torch.tensor(w).reshape(1,-1))
            server = server_module.Server(model, [], aggregation_method='flame_hdbscan', device='cpu')
            server.noise_rng = np.random.default_rng(931)
            context = (patch('sklearn.cluster.HDBSCAN.fit_predict', return_value=np.full(len(u), -1))
                       if force_empty else nullcontext())
            with patch.object(server_module, 'flame_hdbscan', selector), context:
                result = server.aggregate(list(u), list(range(len(u))), round_id=0)
            return result, server.get_global_weights().copy()

        old, old_weights = run(frozen.flame_hdbscan)
        new, new_weights = run(flame_hdbscan)
        telemetry = new['filter_info'].pop('flame_clustering')
        # Independently measured wall-clock durations are not deterministic.
        for result in (old, new):
            for key in ('filter_time', 'aggregation_time', 'root_training_time', 'server_total_time'):
                result.pop(key)
        assert np.array_equal(old_weights, new_weights), name
        assert json.dumps(old, sort_keys=True, default=lambda x:x.tolist()) == json.dumps(new, sort_keys=True, default=lambda x:x.tolist()), name
        comparisons.append(dict(case=name, decision_and_previous_info_equal=True,
                                aggregate_bitwise_equal=True, telemetry=telemetry))
    paths = [frozen_path, root/'new_work/simulation/baselines.py',
             root/'new_work/simulation/server.py', root/'new_work/simulation/run_experiment.py',
             root/'new_work/tests/test_flame_telemetry.py']
    result = dict(cases=comparisons,
                  sources_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  excluded_fields=['flame_clustering (new only)', 'filter_time',
                                   'aggregation_time', 'root_training_time', 'server_total_time'],
                  scope='Same live server; only frozen versus instrumented selector differs. Six synthetic cases.')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(comparisons, indent=2))


if __name__ == '__main__':
    main()
