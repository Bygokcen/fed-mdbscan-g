"""Sequential immutable-source pilot supervisor, diagnostic outputs only."""
import argparse,subprocess,json,os,time,hashlib,fcntl
from pathlib import Path

def save(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)

def check(x):
    assert x['outcome']=='completed';assert len(x['records'])==1;assert len(x['clients'])==90
    for batches in x['clients'].values():
        assert len(batches)==5
        if x['arm'] in ['B','C']:assert all(b['batch_size']==20 for b in batches)
        if x['arm']=='C':assert all(b['batch_sha256']==batches[0]['batch_sha256'] for b in batches)
        assert all('cohort_geometric_median_distance' in b for b in batches)

p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--python',required=True);a=p.parse_args();out=Path(a.output).resolve()
manifest=json.loads((out/'manifest.json').read_text())
for f,h in manifest['files'].items():assert hashlib.sha256((out/f).read_bytes()).hexdigest()==h
check(json.loads((out/'smoke_B.json').read_text()))
status=dict(state='running',pid=os.getpid(),completed=0,total=27,started=time.time());save(out/'status.json',status)
lock=(out/'worker.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
try:
    for ds in manifest['datasets']:
        for seed in manifest['seeds']:
            results={}
            for arm in manifest['arms']:
                name=f'{ds}_{seed}_{arm}';target=out/(name+'.json');assert not target.exists()
                status.update(cell=name,updated=time.time());save(out/'status.json',status)
                with (out/(name+'.log')).open('w') as log:
                    c=subprocess.Popen([a.python,'-u','-m','simulation.batch_control_probe','--config',str(out/'configs'/f'{ds}_{seed}.json'),'--output',str(target),'--arm',arm],cwd=out/'source/new_work',stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),),env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
                    status['child_pid']=c.pid;save(out/'status.json',status);code=c.wait()
                assert code==0,f'{name} failed with exit {code}'
                x=json.loads(target.read_text());check(x);results[arm]=x;status['completed']+=1;save(out/'status.json',status)
            for key in ['partition_sha256','initial_model_sha256','schedule_sha256']:
                assert len({x['metadata'][key] for x in results.values()})==1,(ds,seed,key)
            assert results['B']['records'][0]['server_input_ids']==results['C']['records'][0]['server_input_ids']
            for cid,steps in results['B']['clients'].items():
                assert steps[0]['batch_sha256']==results['C']['clients'][cid][0]['batch_sha256']
                assert steps[0]['delta_sha256']==results['C']['clients'][cid][0]['delta_sha256'],(ds,seed,cid,'first-step RNG differs')
    status['state']='complete'
except BaseException as exc:
    status.update(state='failed',error=repr(exc));raise
finally:
    status.update(updated=time.time(),child_pid=None);save(out/'status.json',status)
