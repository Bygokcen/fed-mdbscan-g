"""Supervisor for the flat-profile de-inflation matrix. Frozen source, sequential."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path('/home/gokcen/Fed_MDBSCAN_TIFS')
HERE = Path(__file__).resolve().parent
OUT_BASE = ROOT / 'new_work/results/temporal_deinflation'
REFERENCE = ROOT / 'new_work/results/cutoff_development/study_20260914_v1/runs'

DATASETS = ['mnist', 'fashion_mnist']
SEEDS = [42, 137, 2024]
METHODS = ['fedavg', 'fed_mdbscan_g']
RATIOS = [1.0, 2.0]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, payload):
    tmp = Path(path).with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, indent=2) + '\n')
    tmp.replace(path)


def prepare():
    sys.path.insert(0, str(ROOT / 'new_work'))
    from simulation.contracts import resolve_experiment_config
    out = OUT_BASE / f'flat_{time.strftime("%Y%m%d_%H%M%S")}'
    out.mkdir(parents=True, exist_ok=False)
    source = out / 'source/new_work'
    source.mkdir(parents=True)
    ignore = shutil.ignore_patterns('__pycache__')
    shutil.copytree(ROOT / 'new_work/simulation', source / 'simulation', ignore=ignore)
    shutil.copytree(ROOT / 'new_work/tests', source / 'tests', ignore=ignore)
    shutil.copy2(HERE / 'worker.py', out / 'worker.py')

    configs = out / 'configs'
    configs.mkdir()
    for dataset in DATASETS:
        for seed in SEEDS:
            # Same protocol as the development study's Min-Max cell; only the
            # attack type and its profile ratio differ.
            reference = json.loads((REFERENCE / f'cutoff_attacked/{dataset}'
                                    / 'scenario_cut_minmax/runs/fedavg_seed42.json').read_text())
            base = dict(reference['config'] if 'config' in reference
                        else reference['resolved_config'])
            for ratio in RATIOS:
                cfg = resolve_experiment_config({
                    **base, 'seed': seed,
                    'attack_type': 'minmax_flat_omniscient',
                    'coordinated_profile_ratio': ratio,
                    'output_dir': str(out / 'diagnostic_unused_output'),
                    'data_dir': str(ROOT / 'new_work/data'),
                })
                save(configs / f'{dataset}_{seed}_r{ratio}.json', cfg)

    manifest = dict(version='temporal-deinflation-v1', created_unix=time.time(),
                    datasets=DATASETS, seeds=SEEDS, methods=METHODS, ratios=RATIOS,
                    expected_cells=len(DATASETS) * len(SEEDS) * len(METHODS) * len(RATIOS),
                    protocol_sha256=sha256(HERE / 'PROTOCOL.md'),
                    files={str(p.relative_to(out)): sha256(p)
                           for p in sorted(out.rglob('*')) if p.is_file()})
    save(out / 'manifest.json', manifest)
    print(json.dumps({'output': str(out), 'cells': manifest['expected_cells']}))
    return out


def run(out, python):
    out = Path(out).resolve()
    manifest = json.loads((out / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if sha256(out / name) != digest:
            raise SystemExit(f'frozen file changed: {name}')
    source = out / 'source/new_work'
    status = dict(state='running', pid=os.getpid(), completed=0,
                  total=manifest['expected_cells'], started=time.time())
    save(out / 'status.json', status)
    try:
        for dataset in manifest['datasets']:
            for seed in manifest['seeds']:
                for ratio in manifest['ratios']:
                    for method in manifest['methods']:
                        name = f'{dataset}_{seed}_r{ratio}_{method}'
                        target = out / 'cells' / f'{name}.json'
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if target.exists():
                            raise SystemExit(f'refusing to overwrite {target}')
                        status.update(cell=name, updated=time.time())
                        save(out / 'status.json', status)
                        with (target.with_suffix('.log')).open('w') as log:
                            code = subprocess.Popen(
                                [python, '-u', str(out / 'worker.py'),
                                 '--config', str(out / 'configs' / f'{dataset}_{seed}_r{ratio}.json'),
                                 '--method', method, '--output', str(target)],
                                cwd=source, stdin=subprocess.DEVNULL,
                                stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, 'OMP_NUM_THREADS': '1',
                                     'MKL_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'},
                            ).wait()
                        if code != 0:
                            raise SystemExit(f'{name} failed with exit {code}')
                        status['completed'] += 1
                        save(out / 'status.json', status)
        status['state'] = 'complete'
    except BaseException as exc:
        status.update(state='failed', error=repr(exc))
        raise
    finally:
        status.update(updated=time.time())
        save(out / 'status.json', status)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prepare', action='store_true')
    p.add_argument('--run')
    p.add_argument('--python', default=str(ROOT / '.venv/bin/python'))
    a = p.parse_args()
    if a.prepare:
        prepare()
    elif a.run:
        run(a.run, a.python)
    else:
        p.error('choose --prepare or --run')


if __name__ == '__main__':
    main()
