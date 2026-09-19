"""Forward-round A/B/C supervisor: frozen source, sequential, never overwrites.

Prepares an immutable run directory, plays one reference trajectory per
(dataset, seed), then replays arms A/B/C from each captured checkpoint. Every
branch is a separate process reading only the reference's checkpoint files, so
no branch result can influence the reference trajectory.

    .venv/bin/python analysis/forward_round_20260913/run_forward.py --prepare
    .venv/bin/python analysis/forward_round_20260913/run_forward.py --run <dir>

Diagnostic outputs only; no canonical unit is written.
"""

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RESULTS = ROOT / 'new_work/results/mechanism_forward_round'
PILOT_STATE = HERE.parent / 'step_control_stratified/current_pilot.json'

DATASETS = ['har', 'mnist', 'fashion_mnist']
SEEDS = [42, 137, 2024]
ARMS = ['A', 'B', 'C']
REFERENCE_ROUNDS = 30
CHECKPOINT_ROUNDS = [0, 9, 19, 29]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, payload):
    tmp = Path(path).with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, indent=2) + '\n')
    tmp.replace(path)


def prepare():
    """Freeze source and configs into a fresh run directory."""
    sys.path.insert(0, str(ROOT / 'new_work'))
    from simulation.contracts import resolve_experiment_config

    pilot = Path(json.loads(PILOT_STATE.read_text())['output'])
    out = RESULTS / f'forward_{time.strftime("%Y%m%d_%H%M%S")}'
    out.mkdir(parents=True, exist_ok=False)

    source = out / 'source/new_work'
    source.mkdir(parents=True)
    ignore = shutil.ignore_patterns('__pycache__')
    shutil.copytree(ROOT / 'new_work/simulation', source / 'simulation', ignore=ignore)
    shutil.copytree(ROOT / 'new_work/tests', source / 'tests', ignore=ignore)

    configs = out / 'configs'
    configs.mkdir()
    for dataset in DATASETS:
        for seed in SEEDS:
            base = json.loads((pilot / f'configs/{dataset}_{seed}.json').read_text())
            base['output_dir'] = str(out / 'diagnostic_unused_output')
            for label, rounds in (('reference', REFERENCE_ROUNDS), ('branch', 1)):
                resolved = resolve_experiment_config(dict(base, num_rounds=rounds))
                save(configs / f'{dataset}_{seed}_{label}.json', resolved)

    manifest = dict(
        version='forward-round-v1',
        created_unix=time.time(),
        datasets=DATASETS, seeds=SEEDS, arms=ARMS,
        reference_rounds=REFERENCE_ROUNDS, checkpoint_rounds=CHECKPOINT_ROUNDS,
        pilot_source=str(pilot.relative_to(ROOT)),
        expected_references=len(DATASETS) * len(SEEDS),
        expected_branches=len(DATASETS) * len(SEEDS) * len(CHECKPOINT_ROUNDS) * len(ARMS),
        files={str(p.relative_to(out)): sha256(p)
               for p in sorted(out.rglob('*')) if p.is_file()},
    )
    save(out / 'manifest.json', manifest)
    print(json.dumps({'output': str(out),
                      'references': manifest['expected_references'],
                      'branches': manifest['expected_branches']}))
    return out


def launch(python, source, args, log_path, extra_fds=()):
    with open(log_path, 'w') as log:
        proc = subprocess.Popen(
            [python, '-u', '-m', 'simulation.forward_round_probe', *args],
            cwd=source, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            pass_fds=tuple(extra_fds),
            env={**os.environ, 'OMP_NUM_THREADS': '1',
                 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'})
        return proc.wait()


def run(out, python):
    out = Path(out).resolve()
    manifest = json.loads((out / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if sha256(out / name) != digest:
            raise SystemExit(f'frozen file changed: {name}')

    source = out / 'source/new_work'
    configs = out / 'configs'
    total = manifest['expected_references'] + manifest['expected_branches']
    status = dict(state='running', pid=os.getpid(), completed=0, total=total,
                  started=time.time())
    save(out / 'status.json', status)

    lock = (out / 'worker.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        for dataset in manifest['datasets']:
            for seed in manifest['seeds']:
                cell = f'{dataset}_{seed}'
                ref_dir = out / 'reference' / cell
                ref_dir.mkdir(parents=True, exist_ok=True)
                ref_json = ref_dir / 'reference.json'
                if ref_json.exists():
                    raise SystemExit(f'refusing to overwrite {ref_json}')

                status.update(cell=f'{cell}/reference', updated=time.time())
                save(out / 'status.json', status)
                code = launch(python, source, [
                    '--mode', 'reference',
                    '--config', str(configs / f'{cell}_reference.json'),
                    '--output', str(ref_json),
                    '--rounds', str(manifest['reference_rounds']),
                    '--checkpoint-rounds', ','.join(str(r) for r in manifest['checkpoint_rounds']),
                ], ref_dir / 'reference.log', (lock.fileno(),))
                if code != 0:
                    raise SystemExit(f'{cell} reference failed with exit {code}')
                reference = json.loads(ref_json.read_text())
                if reference['outcome'] != 'completed':
                    raise SystemExit(f'{cell} reference did not complete')
                status['completed'] += 1
                save(out / 'status.json', status)

                by_round = {r['round']: r for r in reference['records']}
                for checkpoint_round in manifest['checkpoint_rounds']:
                    checkpoint = ref_dir / f'checkpoints/round_{checkpoint_round:03d}.json'
                    arms = {}
                    for arm in manifest['arms']:
                        name = f'{cell}_r{checkpoint_round:03d}_{arm}'
                        target = out / 'branches' / f'{name}.json'
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if target.exists():
                            raise SystemExit(f'refusing to overwrite {target}')
                        status.update(cell=name, updated=time.time())
                        save(out / 'status.json', status)
                        code = launch(python, source, [
                            '--mode', 'branch',
                            '--config', str(configs / f'{cell}_branch.json'),
                            '--output', str(target),
                            '--checkpoint', str(checkpoint),
                            '--arm', arm,
                        ], target.with_suffix('.log'), (lock.fileno(),))
                        if code != 0:
                            raise SystemExit(f'{name} failed with exit {code}')
                        arms[arm] = json.loads(target.read_text())
                        status['completed'] += 1
                        save(out / 'status.json', status)

                    verify_cell(cell, checkpoint_round, arms, by_round[checkpoint_round])
        status['state'] = 'complete'
    except BaseException as exc:
        status.update(state='failed', error=repr(exc))
        raise
    finally:
        status.update(updated=time.time())
        save(out / 'status.json', status)


def verify_cell(cell, checkpoint_round, arms, reference_record):
    """Every arm must start from one shared state; arm A must replay the reference."""
    where = f'{cell}@{checkpoint_round}'
    for key in ('initial_model_sha256', 'partition_sha256', 'schedule_sha256'):
        values = {a['metadata'][key] for a in arms.values()}
        if len(values) != 1:
            raise SystemExit(f'{where}: arms disagree on {key}')

    cohorts = {tuple(a['records'][0]['server_input_ids']) for a in arms.values()}
    if len(cohorts) != 1:
        raise SystemExit(f'{where}: arms disagree on the participating cohort')
    if list(next(iter(cohorts))) != list(reference_record['server_input_ids']):
        raise SystemExit(f'{where}: branch cohort differs from the reference round')

    # The integrity control: arm A is the reference round replayed from its own
    # checkpoint, so it must match bit for bit.
    replay = arms['A']['records'][0]
    for key in ('accuracy', 'fpr', 'tpr', 'n_benign', 'n_anomaly',
                'l0_rejected_count', 'gap_concentration', 'accepted_ids'):
        if replay[key] != reference_record[key]:
            raise SystemExit(f'{where}: arm A diverges from the reference on {key}')
    if replay['update_norms'] != reference_record['update_norms']:
        raise SystemExit(f'{where}: arm A update norms differ from the reference')

    first_b = arms['B']['clients']
    first_c = arms['C']['clients']
    for cid, steps in first_b.items():
        if steps[0]['batch_sha256'] != first_c[cid][0]['batch_sha256']:
            raise SystemExit(f'{where}: B and C differ on client {cid} first batch')
        if steps[0]['delta_sha256'] != first_c[cid][0]['delta_sha256']:
            raise SystemExit(f'{where}: B and C differ on client {cid} first update')
        if any(b['batch_size'] != 20 for b in steps):
            raise SystemExit(f'{where}: arm B batch size is not 20 for client {cid}')
        if any(b['batch_sha256'] != first_c[cid][0]['batch_sha256'] for b in first_c[cid]):
            raise SystemExit(f'{where}: arm C repeated batch is not constant for {cid}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run')
    parser.add_argument('--python', default=str(ROOT / '.venv/bin/python'))
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.run:
        run(args.run, args.python)
    else:
        parser.error('choose --prepare or --run')


if __name__ == '__main__':
    main()
