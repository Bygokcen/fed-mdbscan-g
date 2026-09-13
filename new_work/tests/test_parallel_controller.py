import importlib.util
import json
import signal
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_campaign_parallel as controller
from audit_campaign_guard import validate_science


def test_campaign_lock_excludes_second_controller(tmp_path, monkeypatch):
    monkeypatch.setattr(controller, 'existing_processes', lambda root: [])
    with controller.acquire_lock(tmp_path):
        with pytest.raises(BlockingIOError):
            controller.acquire_lock(tmp_path)
    with controller.acquire_lock(tmp_path):
        pass


def test_stop_exits_with_nonempty_queue(tmp_path, monkeypatch):
    import simulation.run_audit_campaign as campaign
    import audit_campaign_guard as guard
    jobs=[dict(id=f'main/har/{i}', methods=['fedavg'],seeds=[42]) for i in range(2)]
    m={'jobs':jobs,'expected_units':2}
    states=[dict(job=j['id'],valid=0,missing=['fedavg_seed42.json'],failures=[],invalid=[],identities=[]) for j in jobs]
    audit=dict(jobs=states,valid_units=0,expected_units=2,failed_units=0,missing_units=2,invalid_units=0,complete=False)
    monkeypatch.setattr(campaign,'load_manifest',lambda root:m)
    monkeypatch.setattr(campaign,'verify_snapshot',lambda *a:None)
    monkeypatch.setattr(guard,'audit_campaign',lambda *a:audit)
    monkeypatch.setattr(guard,'check_job',lambda root,job,manifest:states[0])
    monkeypatch.setattr(controller,'publish_audit',lambda *a:audit)
    monkeypatch.setattr(controller,'existing_processes',lambda *a:[])
    handlers={};children=[]
    monkeypatch.setattr(controller.signal,'signal',lambda sig,fn:handlers.update({sig:fn}))
    class Child:
        pid=123456;returncode=None
        def __init__(self,*a,**kw):children.append(self)
        def poll(self):return self.returncode
        def terminate(self):self.returncode=-15
        def wait(self):return self.returncode
    monkeypatch.setattr(controller.subprocess,'Popen',Child)
    sleeps=[]
    def sleep(seconds):
        sleeps.append(seconds)
        assert len(sleeps)<3, 'stopping controller did not exit'
        handlers[signal.SIGTERM](signal.SIGTERM,None)
    monkeypatch.setattr(controller.time,'sleep',sleep)
    monkeypatch.setattr(sys,'argv',['runner',str(tmp_path),'--slots','1'])
    assert controller.main()==1
    assert len(children)==1
    status=json.loads((tmp_path/'parallel_progress.json').read_text())
    assert status['state']=='stopped' and not status['complete']
    assert not status['child_pids']


def synthetic_unit():
    from simulation.contracts import resolve_experiment_config,build_participation_schedule
    from simulation.run_batch_experiments import _sha256_json
    c=resolve_experiment_config(dict(num_clients=4,num_rounds=1,malicious_ratio=0,methods=['fedavg']))
    latent,schedule=build_participation_schedule(c,list(range(4)))
    meta=dict(active_client_ids=list(range(4)),latent_malicious_ids=latent,
              participation_schedule=schedule,schedule_sha256=_sha256_json(schedule),
              partition_repair={'after_counts':{str(i):20 for i in range(4)}},
              client_metadata={str(i):dict(sample_count=20,class_histogram={'0':20},size_quartile=i,dominant_label=0) for i in range(4)})
    groups={f'size_quartile:{i}':{'fp':0,'tn':1} for i in range(4)}
    groups['dominant_label:0']={'fp':0,'tn':4}
    r=dict(round=0,actual_malicious_ids=[],participant_ids=schedule[0],scheduled_ids=schedule[0],
           update_ids=[f'0:{i}' for i in schedule[0]],oracle_excluded_ids=[],server_input_ids=schedule[0],
           effective_malicious_ratio=0,attack_active=0,rejected_ids=[],accepted_ids=schedule[0],
           group_confusion=groups,attack_alert=0,alert_tp=0,alert_fp=0,alert_fn=0,alert_tn=1)
    return dict(resolved_config=c,run_metadata=meta,records=[r])


def test_guard_accepts_consistent_evidence():validate_science(synthetic_unit())


@pytest.mark.parametrize('mutation',[lambda u:u['records'][0].update(actual_malicious_ids=[0]),
    lambda u:u['records'][0].update(scheduled_ids=[0]),
    lambda u:u['records'][0]['group_confusion']['dominant_label:0'].update(fp=1),
    lambda u:u['records'][0].update(alert_tp=1),
    lambda u:u['run_metadata'].update(schedule_sha256='wrong')])
def test_guard_rejects_semantic_tampering(mutation):
    from simulation.run_batch_experiments import BatchContractError
    u=synthetic_unit();mutation(u)
    with pytest.raises(BatchContractError):validate_science(u)


def test_failure_outcomes_keep_expected_seed_denominator(tmp_path):
    import pandas as pd
    (tmp_path/'report').mkdir()
    job=dict(id='main/har/3.1',phase='main',dataset='har',scenario={'id':'3.1'},
             methods=['sample_weighted_mean'],seeds=[42,137,2024])
    state=dict(job=job['id'],valid=1,missing=[],invalid=[],failures=[
        dict(method='sample_weighted_mean',seed=42,reason='nonfinite'),
        dict(method='sample_weighted_mean',seed=2024,reason='nonfinite')])
    controller.write_outcomes(tmp_path,{'jobs':[job]},{'jobs':[state]})
    frame=pd.read_csv(tmp_path/'report/cell_status.csv')
    assert frame.iloc[0]['expected_seeds']==3
    assert frame.iloc[0]['valid']==1 and frame.iloc[0]['failed']==2
    assert not frame.iloc[0]['cell_complete']


def test_child_inherits_lock_even_if_controller_closes_it(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setattr(controller,'existing_processes',lambda root:[])
    handle=controller.acquire_lock(tmp_path)
    child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],pass_fds=(handle.fileno(),))
    try:
        handle.close()
        with pytest.raises(BlockingIOError):controller.acquire_lock(tmp_path)
    finally:
        child.terminate();child.wait()
    with controller.acquire_lock(tmp_path):pass
