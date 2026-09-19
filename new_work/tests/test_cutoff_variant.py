import numpy as np
import pytest
from simulation.contracts import resolve_experiment_config
from simulation.run_audit_campaign import plan_jobs, job_config
from simulation import mdbscan

def test_cutoff_variant_has_one_parameter_difference():
    p=resolve_experiment_config({})['method_params']
    assert {k for k in p['fed_mdbscan_g'] if p['fed_mdbscan_g'][k]!=p['mdbg_no_snnc_cutoff'][k]}=={'enable_snnc_cutoff'}
    with pytest.raises(ValueError):
        resolve_experiment_config({'method_params':{'mdbg_no_snnc_cutoff':{'enable_snnc_cutoff':'false'}}})

def test_cutoff_switch_only_changes_snnc_radius_argument(monkeypatch):
    seen=[];original=mdbscan.snnc
    def spy(data,k,eps=None,original_indices=None):
        seen.append(eps)
        return original(data,k,eps=eps,original_indices=original_indices)
    monkeypatch.setattr(mdbscan,'snnc',spy)
    u=np.random.default_rng(4).normal(size=(12,3)).astype(np.float32)
    for enabled in [True,False]:
        mdbscan.fed_mdbscan_g_filter(u,t=100.,eps=.5,attack_history=[True],enable_snnc_cutoff=enabled)
    assert seen==[.5,None]

def test_cutoff_plan_pairs_modes_and_methods(tmp_path):
    jobs=plan_jobs(tmp_path,'cutoff_study')
    assert len(jobs)==12
    assert sum(len(j['methods'])*len(j['seeds']) for j in jobs)==144
    assert {j['dataset'] for j in jobs}=={'mnist','fashion_mnist'}
    for j in jobs:
        c=job_config(tmp_path,j)
        assert c['max_local_steps']==5 and c['malicious_ratio']==.2 and c['num_rounds']==30
        assert c['method_params']['mdbg_no_snnc_cutoff']['enable_snnc_cutoff'] is False
        assert c['root_size']==100 and c['partition_policy']=='repair_minimum'
    for ds in ['mnist','fashion_mnist']:
        subset=[j for j in jobs if j['dataset']==ds]
        for attack in ['gaussian','minmax_omniscient','patch_backdoor']:
            pair=[j for j in subset if j['scenario']['attack_type']==attack]
            configs=[job_config(tmp_path,j) for j in pair]
            for c in configs:
                c.pop('attack_mode');c.pop('output_dir');c.pop('protocol_digest')
            assert configs[0]==configs[1]

def test_cutoff_smoke_exercises_all_attacks_and_methods(tmp_path):
    jobs=plan_jobs(tmp_path,'cutoff_smoke')
    assert len(jobs)==6 and all(j['num_rounds']==1 and j['seeds']==[42] for j in jobs)
    assert sum(len(j['methods'])*len(j['seeds']) for j in jobs)==24
