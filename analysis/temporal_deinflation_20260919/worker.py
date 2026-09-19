"""One cell of the flat-profile matrix. Runs from the frozen source copy."""
import argparse, json, os, sys, time
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
for _v in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ.setdefault(_v, '1')

p = argparse.ArgumentParser()
p.add_argument('--config', required=True)
p.add_argument('--method', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()

from pathlib import Path
# Running a script by absolute path puts the script's directory on sys.path, not
# the working directory, so the frozen source has to be added explicitly.
sys.path.insert(0, os.getcwd())

out = Path(a.output)
if out.exists():
    raise SystemExit(f'refusing to overwrite {out}')

import torch
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

from simulation.run_experiment import run_single_experiment

config = json.loads(Path(a.config).read_text())
started = time.time()
result = dict(method=a.method, config=config, started=started)
try:
    metrics = run_single_experiment(config, a.method, config['seed'])
    result.update(outcome='completed', records=metrics.records,
                  run_metadata=metrics.run_metadata)
except Exception as exc:
    result.update(outcome='failed', error=repr(exc))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str) + '\n')
    raise
result['ended'] = time.time()
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
