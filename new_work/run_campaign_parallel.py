#!/usr/bin/env python3
"""Run an audit campaign's jobs concurrently instead of one at a time.

Why this exists
---------------
The built-in sequential worker pins every BLAS/OMP thread to 1 and runs one
job at a time, so on a 16-core machine it uses one core and leaves the GPU at
~13%. The jobs are independent, so the wall-clock cost is dominated by
scheduling, not by computation.

Why it does not change the science
----------------------------------
Parallelism here is per-process, never per-thread. Every child gets the same
single-thread environment the sequential worker used
(OMP/MKL/OPENBLAS/NUMEXPR=1), so each unit's arithmetic is performed exactly
as before; raising thread counts would change BLAS reduction order and could
perturb floating-point results, which is why it is deliberately not done.

Each child is the campaign's own `--worker --job <id>` entry point, launched
from the frozen source snapshot, so it still verifies the snapshot digests and
the dataset identity before running. Seeds are purpose-derived per unit
(`derive_seed(seed, purpose)`), so partition, attacker assignment,
participation schedule and dropout do not depend on execution order.

Jobs of the same (phase, dataset) share a base output directory, but they own
disjoint `scenario_<id>/` subtrees, so no unit file is ever written by two
children. The only shared files are `master_progress.json` (status only) and
`master_summary.json`, which every job invalidates and which is rebuilt from
the on-disk state at the end; neither carries scientific content.

Unit writes are atomic (tmp + os.replace) and completed units are skipped, so
interrupting this script loses at most the units currently in flight.

Usage
-----
    ./run_campaign_parallel.py results/validated/audit-v2/full_20260910
    ./run_campaign_parallel.py <campaign> --slots 8
    ./run_campaign_parallel.py <campaign> --only main/mnist/3.1   # one job
    ./run_campaign_parallel.py <campaign> --dry-run

Progress is written to `<campaign>/parallel_progress.json` and each job keeps
its own log under `<campaign>/logs/`, exactly as in sequential mode.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

THREAD_PINS = {
    'OMP_NUM_THREADS': '1',
    'MKL_NUM_THREADS': '1',
    'OPENBLAS_NUM_THREADS': '1',
    'NUMEXPR_NUM_THREADS': '1',
    'PYTHONUNBUFFERED': '1',
}


def atomic_json(path, value):
    import tempfile
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.control-', suffix='.json')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def existing_processes(root):
    found = []
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            argv = (entry / 'cmdline').read_bytes().decode().split('\0')
            is_worker = 'simulation.run_audit_campaign' in argv and '--worker' in argv
            is_runner = any(Path(a).name == 'run_campaign_parallel.py' for a in argv[:2])
            if (is_worker or is_runner) and any(str(root) == a or root.name in a for a in argv[1:]):
                found.append(int(entry.name))
        except (OSError, UnicodeError):
            pass
    return found


def acquire_lock(root):
    import fcntl
    handle = (root / 'worker.lock').open('a')
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        conflicts = existing_processes(root)
        if conflicts:
            raise RuntimeError(f'existing campaign processes: {conflicts}')
    except BaseException:
        handle.close()
        raise
    return handle


def publish_audit(root, manifest, audit=None):
    from audit_campaign_guard import audit_campaign
    from simulation.report_audit import report_campaign
    if audit is None:
        audit = audit_campaign(root, manifest)
    atomic_json(root / 'external_validation.json', audit)
    # Report missing/failed conditions too; never drop failed seeds from the denominator.
    report_campaign(root)
    write_outcomes(root, manifest, audit)
    if audit['invalid_units']:
        atomic_json(root / 'report/completeness.json', {
            'complete': False, 'error': 'external scientific validation failed',
            'external_validation': '../external_validation.json'})
        (root / 'report/report.md').write_text('Scientific validation failed. See external_validation.json.\n')
        raise RuntimeError('external scientific validation failed')
    return audit


def write_outcomes(root, manifest, audit):
    import pandas as pd
    states = {r['job']: r for r in audit['jobs']}
    outcomes = []
    for job in manifest['jobs']:
        state = states[job['id']]
        failed = {(r['method'], r['seed']): r for r in state['failures']}
        invalid = {Path(r.get('path', '')).name for r in state['invalid']}
        for method in job['methods']:
            for seed in job['seeds']:
                name = f'{method}_seed{seed}.json'
                status = ('invalid' if name in invalid else 'failed' if (method, seed) in failed
                          else 'missing' if name in state['missing'] else 'valid')
                outcomes.append(dict(phase=job['phase'], dataset=job['dataset'], scenario=job['scenario']['id'],
                    method=method, seed=seed, outcome=status,
                    reason=failed.get((method, seed), {}).get('reason', '')))
    from simulation.run_batch_experiments import _atomic_write_csv
    _atomic_write_csv(str(root / 'report/outcomes.csv'), outcomes)
    coverage = pd.DataFrame(outcomes).groupby(['phase','dataset','scenario','method'])['outcome'].value_counts().unstack(fill_value=0)
    for col in ['valid','failed','missing','invalid']:
        if col not in coverage: coverage[col] = 0
    coverage['expected_seeds'] = coverage.sum(axis=1)
    coverage['cell_complete'] = coverage['valid'] == coverage['expected_seeds']
    _atomic_write_csv(str(root / 'report/cell_status.csv'), coverage.reset_index().to_dict('records'))
    with (root / 'report/report.md').open('a') as f:
        f.write('\n\nEk doğrulama: external_validation.json. Tüm beklenen tohumların durumları outcomes.csv ve cell_status.csv içindedir. '
                'Eksik/başarısız tohumu olan hücrelerde cells.csv ortalamaları yalnızca başarılı koşullara aittir; '
                'tam üç-tohum sonucu veya yöntem üstünlüğü olarak kullanılamaz. Sayısal başarısızlıklar sıfır doğrulukla doldurulmaz.\n')


def main():
    parser = argparse.ArgumentParser(description='Validated parallel controller for frozen audit campaigns')
    parser.add_argument('campaign')
    parser.add_argument('--slots', type=int, default=10)
    parser.add_argument('--only', action='append')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--retry-failed', action='store_true', help='explicitly retry recorded failures once')
    args = parser.parse_args()
    if args.slots < 1:
        parser.error('--slots must be positive')
    root = Path(args.campaign).resolve()
    os.environ.update(THREAD_PINS)
    sys.path.insert(0, str(root / 'source/new_work'))
    import torch
    torch.set_num_threads(1)
    from simulation.run_audit_campaign import load_manifest, verify_snapshot
    from audit_campaign_guard import audit_campaign, check_job
    manifest = load_manifest(root)
    verify_snapshot(root, manifest)
    selected = manifest['jobs']
    if args.only:
        unknown = set(args.only) - {j['id'] for j in selected}
        if unknown:
            parser.error(f'unknown job IDs: {sorted(unknown)}')
        selected = [j for j in selected if j['id'] in args.only]
    with acquire_lock(root) as lock:
        audit = audit_campaign(root, manifest)
        atomic_json(root / 'external_validation.json', audit)
        if audit['invalid_units']:
            raise RuntimeError('invalid existing evidence; see external_validation.json')
        states = {r['job']: r for r in audit['jobs']}
        queue = [j for j in selected if states[j['id']]['missing'] or
                 (args.retry_failed and states[j['id']]['failures'])]
        queue.sort(key=lambda j: len(j['methods']) * len(j['seeds']), reverse=True)
        if args.dry_run:
            print(json.dumps({'valid_units': audit['valid_units'], 'failed_units': audit['failed_units'],
                              'queued_jobs': [j['id'] for j in queue]}))
            return 0
        publish_audit(root, manifest, audit)
        running, failed, completed = {}, [], []
        stopping = False
        started = time.time()
        def stop(signum, frame):
            nonlocal stopping
            stopping = True
            for child, handle, job in list(running.values()):
                if child.poll() is None:
                    child.terminate()
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        status = {'pid': os.getpid(), 'mode': 'parallel', 'slots': args.slots,
                  'expected_units': manifest['expected_units'], 'complete': False}
        try:
            while (queue and not stopping) or running:
                while queue and len(running) < args.slots and not stopping:
                    job = queue.pop(0)
                    path = root / 'logs' / (job['id'].replace('/', '_') + '.log')
                    path.parent.mkdir(exist_ok=True)
                    handle = path.open('a')
                    handle.write('\n=== validated parallel controller ===\n'); handle.flush()
                    child = subprocess.Popen([sys.executable, '-u', '-m', 'simulation.run_audit_campaign',
                        '--worker', '--campaign', str(root), '--job', job['id']],
                        cwd=root / 'source/new_work', env={**os.environ, **THREAD_PINS},
                        stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT,
                        pass_fds=(lock.fileno(),))
                    running[child.pid] = (child, handle, job)
                    print(f"start {job['id']} PID={child.pid}", flush=True)
                for pid, (child, handle, job) in list(running.items()):
                    if child.poll() is None:
                        continue
                    handle.close(); del running[pid]
                    state = check_job(root, job, manifest)
                    states[job['id']] = state
                    if state['invalid']:
                        raise RuntimeError(f"invalid new evidence: {job['id']}")
                    ok = child.returncode == 0 and not state['missing'] and not state['failures']
                    (completed if ok else failed).append(job['id'])
                    print(f"{'done' if ok else 'incomplete'} {job['id']}: {state['valid']} valid", flush=True)
                status.update(state='stopping' if stopping else 'running',
                    in_flight=[j['id'] for _, _, j in running.values()], child_pids=list(running),
                    queued=len(queue), completed_jobs=completed, failed_jobs=failed,
                    valid_units=sum(r['valid'] for r in states.values()),
                    units=len(list(root.glob('runs/*/*/scenario_*/runs/*.json'))),
                    failed_units=sum(len(r['failures']) for r in states.values()),
                    updated_unix=time.time(), elapsed_seconds=time.time()-started)
                atomic_json(root / 'parallel_progress.json', status)
                if running or (queue and not stopping):
                    time.sleep(5)
            audit = publish_audit(root, manifest)
            status.update(state='stopped' if stopping else ('complete' if audit['complete'] else 'incomplete'),
                          complete=audit['complete'], valid_units=audit['valid_units'],
                          failed_units=audit['failed_units'], missing_units=audit['missing_units'])
        except BaseException as exc:
            status.update(state='failed', complete=False, error=str(exc))
            raise
        finally:
            for child, handle, job in running.values():
                if child.poll() is None:
                    child.terminate()
                child.wait(); handle.close()
            status.update(updated_unix=time.time(), in_flight=[], child_pids=[])
            atomic_json(root / 'parallel_progress.json', status)
        return 0 if status['complete'] else 1


if __name__ == '__main__':
    sys.exit(main())
