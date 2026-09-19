"""Frozen-source, resumable local audit campaign. No legacy result is reused."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback

from simulation.contracts import resolve_experiment_config
from simulation.run_batch_experiments import (
    SCENARIOS, _atomic_write_json, _sha256_file, _sha256_json,
    _source_state, _environment_state, run_scenario,
)

PRIMARY = ['fed_mdbscan_g', 'fedavg', 'sample_weighted_mean', 'norm_clip',
           'coord_median', 'krum_bound30', 'fltrust_normalized', 'flame_hdbscan']
ABLATIONS = ['mdbg_l0_only', 'mdbg_no_momentum', 'mdbg_no_valve',
             'mdbg_rtr15', 'mdbg_rtr20', 'mdbg_rtr30', 'fed_g2l_25']
SEEDS = [42, 137, 2024]
# Fixed local step budgets for the step-control profile. Together with the
# canonical three-epoch arm these give three points on the local-effort axis,
# which is what makes the relationship readable as a trend rather than a
# single contrast.
STEP_BUDGETS = [5, 20]


def plan_jobs(data_dir, profile='full', step_budgets=None):
    jobs = []
    scenarios = {s['id']: s for s in SCENARIOS}
    for sid, attack, alpha in [('7.1', 'minmax_omniscient', .1),
                               ('7.2', 'minsum_omniscient', .01),
                               ('8.1', 'patch_backdoor', .1),
                               ('8.2', 'patch_backdoor', .01)]:
        scenarios[sid] = dict(id=sid, alpha=alpha, malicious_ratio=.3,
                              attack_type=attack, label=f'{attack}; alpha={alpha}')

    def add(phase, dataset, sid, methods, **overrides):
        jobs.append(dict(id=f'{phase}/{dataset}/{sid}', phase=phase, dataset=dataset,
                         scenario=scenarios[sid], methods=list(methods), seeds=SEEDS,
                         num_clients=100, num_rounds=30, dropout_rate=.1, data_size_sigma=.5,
                         config_overrides={'data_dir': str(Path(data_dir).resolve()), **overrides}))

    if profile in ('cutoff_study', 'cutoff_smoke'):
        methods = ['fed_mdbscan_g', 'mdbg_no_snnc_cutoff', 'mdbg_l0_only', 'fedavg']
        for dataset in (['mnist'] if profile == 'cutoff_smoke' else ['mnist', 'fashion_mnist']):
            for sid, attack, alpha in [('cut_gaussian', 'gaussian', .01),
                                       ('cut_minmax', 'minmax_omniscient', .01),
                                       ('cut_backdoor', 'patch_backdoor', .1)]:
                scenarios[sid] = dict(id=sid, alpha=alpha, malicious_ratio=.2,
                                     attack_type=attack, label=sid)
                for mode in ['clean', 'attacked']:
                    add('cutoff_' + mode, dataset, sid, methods,
                        attack_mode=mode, max_local_steps=5, gaussian_std=5.,
                        backdoor_fraction=.2, backdoor_target=0, backdoor_patch_size=3,
                        attack_start_round=0, attack_end_round=None)
        if profile == 'cutoff_smoke':
            for job in jobs:
                job['num_rounds'] = 1
                job['seeds'] = [42]
        assert len({j['id'] for j in jobs}) == len(jobs)
        return jobs

    if profile == 'smoke':
        for sid in ['6.2', '3.3', '7.1', '7.2']:
            add('main', 'har', sid, PRIMARY + ['mdbg_l0_only'])
        for mode in ['clean', 'oracle']:
            add(mode, 'har', '3.3', ['fed_mdbscan_g', 'fedavg'], attack_mode=mode)
        add('temporal', 'har', '3.1', ['fed_mdbscan_g'], attack_start_round=1, attack_end_round=2)
        add('main', 'mnist', '8.1', ['fed_mdbscan_g', 'fedavg'])
        add('main', 'cifar10', '8.1', ['fed_mdbscan_g', 'krum_bound30', 'flame_hdbscan'])
        for job in jobs:
            job['seeds'] = [42]
            job['num_rounds'] = 2
            job['config_overrides']['max_local_steps'] = 1
        return jobs

    if profile == 'step_control':
        # Local-step control block. The canonical matrix trains three local
        # epochs, so a client's optimizer step count -- and therefore its
        # update norm -- scales with its local dataset size. This block holds
        # the cohort, partition and seeds fixed and varies only the local step
        # budget, which separates "rejected because the update is far" from
        # "rejected because the client holds more data".
        #
        # 6.2 is attack-free, so every rejection is a false positive and the
        # attacker-side confound is absent. 3.1 is the matched attacked
        # condition: the loud Gaussian attack is the one the trust region does
        # detect, so it distinguishes "size bias removed" from "filter simply
        # stopped rejecting anything". Both readings are needed; the clean
        # condition alone cannot tell them apart.
        #
        # fltrust_normalized is retained deliberately as a sign control: it
        # rescales updates to the root-update norm, so if update magnitude is
        # the mechanism, it should not follow the other methods.
        step_methods = ['fed_mdbscan_g', 'mdbg_l0_only', 'flame_hdbscan',
                        'krum_bound30', 'fltrust_normalized', 'fedavg']
        for budget in (step_budgets or STEP_BUDGETS):
            for dataset in ['har', 'mnist', 'fashion_mnist']:
                for sid in ['6.2', '3.1']:
                    add(f'step_control_{budget}', dataset, sid, step_methods,
                        max_local_steps=budget)
            # CIFAR carries no tuned convergence claim and has a narrower
            # reference arm in the canonical matrix, so only the conditions and
            # methods that actually have a three-epoch counterpart are run.
            add(f'step_control_{budget}', 'cifar10', '6.2',
                ['fed_mdbscan_g', 'fedavg', 'flame_hdbscan'],
                max_local_steps=budget)
        assert len({j['id'] for j in jobs}) == len(jobs)
        return jobs

    # Severe clean and attack conditions are first so critical evidence arrives early.
    ordered = ['6.2', '3.3', '4.2', '5.2', '6.1', '3.1']
    ordered += [s['id'] for s in SCENARIOS if s['id'] not in ordered]
    for dataset in ['har', 'mnist', 'fashion_mnist']:
        for sid in ordered:
            add('main', dataset, sid, PRIMARY)
        for sid in ['6.2', '3.3', '4.2', '5.2']:
            add('ablation', dataset, sid, ABLATIONS)
        for sid in ['3.1', '3.3', '4.2', '5.2']:
            add('clean', dataset, sid, ['fed_mdbscan_g', 'fedavg'], attack_mode='clean')
            add('oracle', dataset, sid, ['fedavg'], attack_mode='oracle')
        for sid in ['2.1', '3.1']:
            add('temporal', dataset, sid, ['fed_mdbscan_g', 'mdbg_no_momentum'],
                attack_start_round=10, attack_end_round=20)
        for sid in ['6.2', '3.3']:
            add('preserve_empty', dataset, sid, ['fed_mdbscan_g', 'mdbg_l0_only', 'fed_g2l_25'],
                partition_policy='preserve_empty')
        for sid in ['3.3', '5.2']:
            add('fixed_steps', dataset, sid, ['fed_mdbscan_g', 'mdbg_l0_only', 'fedavg'],
                max_local_steps=5)
        for sid in ['7.1', '7.2']:
            add('main', dataset, sid, PRIMARY + ['mdbg_l0_only'])
            add('clean', dataset, sid, ['fed_mdbscan_g', 'fedavg'], attack_mode='clean')
            add('oracle', dataset, sid, ['fedavg'], attack_mode='oracle')
        if dataset != 'har':
            for sid in ['8.1', '8.2']:
                add('main', dataset, sid, ['fed_mdbscan_g', 'mdbg_l0_only', 'fedavg',
                                          'fltrust_normalized', 'flame_hdbscan'])
                add('clean', dataset, sid, ['fed_mdbscan_g', 'fedavg'], attack_mode='clean')
                add('oracle', dataset, sid, ['fedavg'], attack_mode='oracle')
    # Explicitly exploratory: this CNN task has no tuned convergence claim.
    for sid in ['6.1', '6.2', '7.1', '7.2', '8.1', '8.2']:
        add('main', 'cifar10', sid, ['fed_mdbscan_g', 'fedavg', 'flame_hdbscan'])
        if sid.startswith(('7', '8')):
            add('clean', 'cifar10', sid, ['fed_mdbscan_g', 'fedavg'], attack_mode='clean')
            add('oracle', 'cifar10', sid, ['fedavg'], attack_mode='oracle')
    assert len({j['id'] for j in jobs}) == len(jobs)
    return jobs


def job_output(root, job):
    return Path(root) / 'runs' / job['phase'] / job['dataset']


def job_config(root, job):
    s = job['scenario']
    return resolve_experiment_config(dict(
        dataset=job['dataset'], num_clients=job['num_clients'], num_rounds=job['num_rounds'],
        local_epochs=3, lr=.01, non_iid_alpha=s['alpha'], malicious_ratio=s['malicious_ratio'],
        attack_type=s['attack_type'], iid=False, dropout_rate=job['dropout_rate'],
        data_size_sigma=job['data_size_sigma'], **job['config_overrides'],
        output_dir=str(job_output(root, job) / f"scenario_{s['id']}"), methods=job['methods']))


def load_manifest(root):
    manifest = json.loads((Path(root) / 'campaign.json').read_text())
    unsigned = dict(manifest)
    digest = unsigned.pop('manifest_sha256')
    if digest != _sha256_json(unsigned):
        raise ValueError('campaign manifest checksum mismatch')
    return manifest


def verify_snapshot(root, manifest):
    source = Path(root) / 'source'
    for relative, digest in manifest['snapshot_files'].items():
        if _sha256_file(source / relative) != digest:
            raise ValueError(f'frozen source changed: {relative}')
    if _source_state() != manifest['source']:
        raise ValueError('worker must run from the exact frozen source')
    if _environment_state() != manifest['environment']:
        raise ValueError('campaign environment changed; use a new campaign')


def create_campaign(root, data_dir, profile, step_budgets=None):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    original = Path(__file__).resolve().parents[2]
    source = root / 'source'
    target = source / 'new_work'
    target.mkdir(parents=True)
    shutil.copytree(Path(__file__).parent, target / 'simulation', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(original / 'new_work/tests', target / 'tests', ignore=shutil.ignore_patterns('__pycache__'))
    for name in ['requirements.txt', 'requirements-dev.txt']:
        if (original / name).exists():
            shutil.copy2(original / name, source / name)
    provenance = _source_state()
    _atomic_write_json(str(source / 'source_provenance.json'), provenance)
    freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
    (source / 'pip-freeze.txt').write_text(freeze.stdout)
    from simulation.data_distributor import load_dataset
    from simulation.run_experiment import _dataset_identity
    jobs = plan_jobs(data_dir, profile, step_budgets=step_budgets)
    dataset_identities = {}
    for name in sorted({j['dataset'] for j in jobs}):
        train, test = load_dataset(name, str(Path(data_dir).resolve()))
        dataset_identities[name] = {'name': name, 'train': _dataset_identity(train),
                                    'test': _dataset_identity(test)}
        del train, test
    manifest = dict(version='audit-campaign-v1', profile=profile, created_unix=time.time(),
                    source=provenance, environment=_environment_state(),
                    jobs=jobs, dataset_identities=dataset_identities, snapshot_files={})
    for path in sorted(source.rglob('*')):
        if path.is_file():
            manifest['snapshot_files'][str(path.relative_to(source))] = _sha256_file(path)
    for job in manifest['jobs']:
        job_config(root, job)  # reject invalid plans before any training
    manifest['expected_units'] = sum(len(j['methods']) * len(j['seeds']) for j in manifest['jobs'])
    manifest['manifest_sha256'] = _sha256_json(manifest)
    _atomic_write_json(str(root / 'campaign.json'), manifest)
    return root


def launch(root):
    root = Path(root).resolve()
    with (root / 'worker.log').open('a') as log:
        child = subprocess.Popen([sys.executable, '-u', '-m', 'simulation.run_audit_campaign',
                                  '--worker', '--campaign', str(root)],
                                 cwd=root / 'source/new_work', stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                                 env={**os.environ, 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
                                      'OPENBLAS_NUM_THREADS': '1', 'PYTHONUNBUFFERED': '1'})
    _atomic_write_json(str(root / 'launch.json'), {'pid': child.pid, 'started_unix': time.time()})
    return child.pid


def worker(root, one_job=None):
    root = Path(root).resolve()
    manifest = load_manifest(root)
    verify_snapshot(root, manifest)
    if one_job is not None:
        job = next(j for j in manifest['jobs'] if j['id'] == one_job)
        from simulation.data_distributor import load_dataset
        from simulation.run_experiment import _dataset_identity
        train, test = load_dataset(job['dataset'], job['config_overrides']['data_dir'])
        current_data = {'name': job['dataset'], 'train': _dataset_identity(train), 'test': _dataset_identity(test)}
        if current_data != manifest['dataset_identities'][job['dataset']]:
            raise ValueError('dataset content changed since campaign creation')
        del train, test
        summary = run_scenario(job['scenario'], base_output_dir=str(job_output(root, job)),
                     **{k: job[k] for k in ['dataset', 'num_clients', 'num_rounds', 'seeds',
                                           'dropout_rate', 'data_size_sigma', 'methods', 'config_overrides']})
        if not summary.get('complete'):
            raise RuntimeError(f'incomplete job: {one_job}')
        return
    def interrupted(signum, frame):
        raise InterruptedError(f'campaign interrupted by signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    with (root / 'worker.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        from simulation.report_audit import report_campaign
        status = dict(pid=os.getpid(), state='running', expected_units=manifest['expected_units'])
        child = None
        try:
            for index, job in enumerate(manifest['jobs']):
                status.update(job=job['id'], job_index=index, updated_unix=time.time())
                _atomic_write_json(str(root / 'status.json'), status)
                log_path = root / 'logs' / (job['id'].replace('/', '_') + '.log')
                log_path.parent.mkdir(exist_ok=True)
                with log_path.open('a') as log:
                    child = subprocess.Popen([sys.executable, '-u', '-m', 'simulation.run_audit_campaign',
                                              '--worker', '--job', job['id'], '--campaign', str(root)],
                                             stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
                    status['child_pid'] = child.pid
                    while child.poll() is None:
                        status['updated_unix'] = time.time()
                        status['written_units'] = len(list((root / 'runs').glob('*/*/scenario_*/runs/*.json')))
                        _atomic_write_json(str(root / 'status.json'), status)
                        time.sleep(10)
                if child.returncode:
                    raise RuntimeError(f"job {job['id']} failed ({child.returncode}); see {log_path}")
                summary = report_campaign(root)
                status['valid_units'] = summary['valid_units']
                print(f"Completed {job['id']}: {summary['valid_units']}/{manifest['expected_units']}", flush=True)
            if not summary['complete']:
                raise RuntimeError('campaign still has missing units; see report/completeness.json')
            status.update(state='complete', complete=True)
        except BaseException as exc:
            if child is not None and child.poll() is None:
                child.terminate()
                child.wait()
            status.update(state='failed', complete=False, error=str(exc))
            traceback.print_exc()
            raise
        finally:
            status['updated_unix'] = time.time()
            _atomic_write_json(str(root / 'status.json'), status)


def main():
    import torch
    torch.set_num_threads(1)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', required=True)
    parser.add_argument('--data-dir', default='./data')
    parser.add_argument('--profile', choices=['full', 'smoke', 'step_control', 'cutoff_study', 'cutoff_smoke'],
                        default='full')
    parser.add_argument('--step-budgets', dest='step_budgets',
                        type=lambda v: [int(x) for x in v.split(',') if x],
                        default=None,
                        help='step_control only: comma separated local step '
                             'budgets, e.g. 5 or 5,20 (default: %(default)s -> '
                             f'{STEP_BUDGETS})')
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--job')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    execution_profile = (load_manifest(args.campaign)['profile']
                         if args.worker or args.resume else args.profile)
    if execution_profile in ('cutoff_study', 'cutoff_smoke'):
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        if not torch.cuda.is_available():
            raise RuntimeError('cutoff study requires the validated CUDA environment')
    if args.worker:
        worker(args.campaign, args.job)
    else:
        root = Path(args.campaign).resolve()
        if not args.resume:
            create_campaign(root, args.data_dir, args.profile,
                            step_budgets=args.step_budgets)
        print(json.dumps({'campaign': str(root), 'pid': launch(root),
                          'expected_units': load_manifest(root)['expected_units']}))


if __name__ == '__main__':
    main()
