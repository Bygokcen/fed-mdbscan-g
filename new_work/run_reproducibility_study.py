"""Sequential controlled probes, with the campaign lock held by parent and child."""
import argparse,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from run_campaign_parallel import acquire_lock,atomic_json,THREAD_PINS


def main():
    p=argparse.ArgumentParser();p.add_argument('campaign');p.add_argument('--output',required=True);a=p.parse_args()
    root=Path(a.campaign).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    jobs=[('normal_a',[]),('normal_b',[]),('observed_a',['--observe-sgd']),
          ('deterministic_a',['--deterministic']),('deterministic_b',['--deterministic']),
          ('deterministic_observed',['--deterministic','--observe-sgd'])]
    child=None;status=dict(pid=os.getpid(),state='running',started_unix=time.time())
    def stopped(signum,frame):raise InterruptedError(f'signal {signum}')
    signal.signal(signal.SIGTERM,stopped);signal.signal(signal.SIGINT,stopped)
    with acquire_lock(root) as lock:
        try:
            for name,flags in jobs:
                status.update(job=name,updated_unix=time.time());atomic_json(out/'status.json',status)
                with (out/(name+'.log')).open('w') as log:
                    child=subprocess.Popen([sys.executable,'-u',str(Path(__file__).with_name('probe_cifar_reproducibility.py')),
                        str(root),'--output',str(out/(name+'.json')),*flags],env={**os.environ,**THREAD_PINS},
                        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),))
                    status['child_pid']=child.pid
                    while child.poll() is None:
                        status['updated_unix']=time.time();atomic_json(out/'status.json',status);time.sleep(5)
                if child.returncode:raise RuntimeError(f'probe process failed: {name}')
            comparisons=[]
            for left,right in [('normal_a','normal_b'),('normal_a','observed_a'),
                               ('deterministic_a','deterministic_b'),('deterministic_a','deterministic_observed')]:
                x=json.loads((out/(left+'.json')).read_text());y=json.loads((out/(right+'.json')).read_text())
                diffs=[dict(index=i,left=u,right=v) for i,(u,v) in enumerate(zip(x['trace'],y['trace'])) if u!=v]
                comparisons.append(dict(left=left,right=right,outcomes=[x['outcome'],y['outcome']],
                    trace_counts=[len(x['trace']),len(y['trace'])],different_trace_entries=len(diffs),
                    first_difference=diffs[0] if diffs else None,
                    same_partition=x['run_metadata'].get('partition_sha256')==y['run_metadata'].get('partition_sha256'),
                    same_initial=x['run_metadata'].get('initial_model_sha256')==y['run_metadata'].get('initial_model_sha256')))
            atomic_json(out/'comparisons.json',comparisons);status['state']='complete'
        except BaseException as exc:
            status.update(state='failed',error=str(exc));traceback.print_exc();raise
        finally:
            if child is not None and child.poll() is None:child.terminate();child.wait()
            status.update(child_pid=None,updated_unix=time.time());atomic_json(out/'status.json',status)

if __name__=='__main__':main()
