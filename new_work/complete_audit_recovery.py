"""One-worker retries, immutable attempt history, then observation-only diagnostics."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''): h.update(chunk)
    return h.hexdigest()


def classification(diagnostic):
    if diagnostic.get('outcome') == 'completed':
        return 'not_reproduced_in_observed_replay'
    if any(e.get('stage') == 'nonfinite_local_parameters_after_SGD_step' for e in diagnostic.get('events', [])):
        return 'reproduced_nonfinite_local_training'
    return 'unresolved_failure'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign'); parser.add_argument('--attempt', required=True)
    args = parser.parse_args()
    root, attempt = Path(args.campaign).resolve(), Path(args.attempt).resolve()
    control = Path(__file__).resolve().parent
    from run_campaign_parallel import atomic_json, THREAD_PINS, acquire_lock
    os.environ.update(THREAD_PINS)
    attempt.mkdir(parents=True, exist_ok=True)
    state = dict(pid=os.getpid(), state='preparing', slots=1, attempt=str(attempt), started_unix=time.time())
    child = None
    def publish(**changes):
        state.update(changes, updated_unix=time.time())
        atomic_json(root/'recovery_status.json', state)
        atomic_json(attempt/'status.json', state)
    def stop(signum, frame):
        raise InterruptedError(f'recovery interrupted by signal {signum}')
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    with (root/'recovery.lock').open('a') as recovery_lock:
        fcntl.flock(recovery_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            if (attempt/'before.json').exists():
                raise FileExistsError('Use a fresh attempt directory; previous evidence is immutable')
            publish()
            import shutil
            # Exclude an existing worker while recording the exact starting evidence.
            with acquire_lock(root):
                paths = sorted(root.glob('runs/*/*/scenario_*/runs/*.json'))
                preserved = {str(p.relative_to(root)): file_hash(p) for p in paths}
                failures = list(root.glob('runs/*/*/scenario_*/failures/*.json'))
                for p in failures:
                    target = attempt/'before'/p.relative_to(root)
                    target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, target)
                for name in ['campaign.json','external_validation.json','parallel_progress.json']:
                    shutil.copy2(root/name, attempt/('before_'+name))
                for job in json.loads((root/'campaign.json').read_text())['jobs']:
                    log = root/'logs'/(job['id'].replace('/','_')+'.log')
                    directory=root/'runs'/job['phase']/job['dataset']/f"scenario_{job['scenario']['id']}"
                    if (directory/'failures').exists() or len(list((directory/'runs').glob('*.json'))) < len(job['methods'])*len(job['seeds']):
                        if log.exists(): shutil.copy2(log, attempt/('before_log_'+log.name))
                atomic_json(attempt/'before.json', dict(successful_files=preserved,
                    original_failure_files=len(failures), created_unix=time.time()))
            publish(state='retrying', preserved_units=len(preserved))
            command=[sys.executable,'-u',str(control/'run_campaign_parallel.py'),str(root),'--slots','1','--retry-failed']
            with (attempt/'retry.log').open('a') as log:
                child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                                       env={**os.environ,**THREAD_PINS},pass_fds=(recovery_lock.fileno(),))
                publish(child_pid=child.pid)
                while child.poll() is None:
                    publish(); time.sleep(10)
            progress=json.loads((root/'parallel_progress.json').read_text())
            if child.returncode not in (0,1) or progress['state'] not in ('complete','incomplete'):
                raise RuntimeError(f'retry controller failed: exit={child.returncode}, state={progress.get("state")}')
            child=None
            sys.path.insert(0,str(root/'source/new_work'))
            import torch
            torch.set_num_threads(1)
            from simulation.run_audit_campaign import load_manifest,verify_snapshot
            from run_campaign_parallel import publish_audit
            manifest=load_manifest(root);verify_snapshot(root,manifest)
            diagnoses=[]
            with acquire_lock(root) as worker_lock:
                audit=json.loads((root/'external_validation.json').read_text())
                remaining=[(job['job'], failure) for job in audit['jobs'] for failure in job['failures']]
                for job_id,failure in remaining:
                    stem=job_id.replace('/','_')+f"_{failure['method']}_seed{failure['seed']}"
                    target=attempt/'diagnostics'/f'{stem}.json';target.parent.mkdir(exist_ok=True)
                    publish(state='diagnosing', job=job_id, method=failure['method'], seed=failure['seed'])
                    with (attempt/(stem+'.log')).open('a') as log:
                        child=subprocess.Popen([sys.executable,'-u',str(control/'diagnose_failed_units.py'),str(root),
                            '--job',job_id,'--method',failure['method'],'--seed',str(failure['seed']),
                            '--output',str(target)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                            env={**os.environ,**THREAD_PINS},pass_fds=(worker_lock.fileno(),recovery_lock.fileno()))
                        publish(child_pid=child.pid)
                        while child.poll() is None:
                            publish();time.sleep(10)
                    if child.returncode or not target.exists():
                        diagnoses.append(dict(job=job_id,method=failure['method'],seed=failure['seed'],classification='diagnostic_process_failed'))
                    else:
                        d=json.loads(target.read_text())
                        diagnoses.append(dict(job=job_id,method=failure['method'],seed=failure['seed'],
                            classification=classification(d),events=d.get('events',[]),error=d.get('error'),
                            diagnostic=str(target),sha256=file_hash(target)))
                    child=None
                    atomic_json(attempt/'diagnoses.json',diagnoses)
                publish(state='final_validation',child_pid=None)
                audit=publish_audit(root,manifest)
                changed=[name for name,h in preserved.items() if not (root/name).exists() or file_hash(root/name)!=h]
                if changed:raise RuntimeError(f'Previously successful evidence changed: {changed}')
                report=dict(valid_units=audit['valid_units'],expected_units=audit['expected_units'],
                    failed_units=audit['failed_units'],missing_units=audit['missing_units'],invalid_units=audit['invalid_units'],
                    successful_original_files_unchanged=True,original_valid_units=len(preserved),diagnoses=diagnoses,
                    complete=audit['complete'],finished_unix=time.time())
                atomic_json(attempt/'recovery_report.json',report)
                text=(f"# Eksik deneylerin tamamlanması\n\nDoğrulanmış başarılı birim: {audit['valid_units']}/{audit['expected_units']}. "
                    f"Başarısız: {audit['failed_units']}; eksik: {audit['missing_units']}; geçersiz: {audit['invalid_units']}.\n\n"
                    f"Başlangıçtaki {len(preserved)} başarılı dosyanın tamamı değişmeden korundu. "
                    "Tek işçiyle tekrar koşuldu; başarısız tohumlar değiştirilmedi. "
                    "Başarısız tekrarlar başarılı sonuç yerine konmadı.\n\n")
                for d in diagnoses:text+=f"- {d['job']} / {d['method']} / seed {d['seed']}: {d['classification']}\n"
                (attempt/'recovery_report.md').write_text(text)
            publish(state='complete' if audit['complete'] else 'finished_with_unresolved_results',child_pid=None,
                    valid_units=audit['valid_units'],failed_units=audit['failed_units'],missing_units=audit['missing_units'])
        except BaseException as exc:
            if child is not None and child.poll() is None:
                child.terminate();child.wait()
            publish(state='interrupted' if isinstance(exc,InterruptedError) else 'failed',child_pid=None,error=str(exc))
            traceback.print_exc();raise

if __name__=='__main__':main()
