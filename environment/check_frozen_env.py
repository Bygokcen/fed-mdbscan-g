"""Compare the running interpreter with the canonical campaign's recorded environment.

canonical_environment.json is the `environment` block of the canonical
campaign.json (audit-v2/full_20260910). The fields are read the same way as
_environment_state() in the frozen run_batch_experiments.py.

Run it with the interpreter of the environment to check:
    .venv-frozen/bin/python environment/check_frozen_env.py
Exit status 1 when Python, a package version, or the deterministic flag differs.
Platform and CUDA availability depend on the machine and are only reported.
"""
import json
import pathlib
import platform
import sys

import numpy as np
import pandas as pd
import scipy
import sklearn
import torch

REQUIRED = ('python', 'numpy', 'pandas', 'scipy', 'scikit_learn', 'torch', 'deterministic_backend')
REPORTED = ('cuda_available', 'platform')

recorded = json.loads(pathlib.Path(__file__).with_name('canonical_environment.json').read_text())
current = {
    'python': platform.python_version(),
    'platform': platform.platform(),
    'numpy': np.__version__,
    'pandas': pd.__version__,
    'scipy': scipy.__version__,
    'scikit_learn': sklearn.__version__,
    'torch': torch.__version__,
    'deterministic_backend': bool(torch.are_deterministic_algorithms_enabled()),
    'cuda_available': bool(torch.cuda.is_available()),
}

mismatches = []
for key in REQUIRED + REPORTED:
    same = current[key] == recorded[key]
    if key in REQUIRED and not same:
        mismatches.append(key)
    status = 'ok' if same else ('DIFFERS' if key in REQUIRED else 'differs (machine-specific)')
    print(f'{key:22} recorded={recorded[key]!s:48} current={current[key]!s:48} {status}')

if mismatches:
    print('environment differs from the canonical record: ' + ', '.join(mismatches))
    sys.exit(1)
print('environment matches the canonical record')
