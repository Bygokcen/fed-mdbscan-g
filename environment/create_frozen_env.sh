#!/usr/bin/env bash
# Rebuild the canonical experiment environment from its pip freeze and check
# that the result matches the frozen record.
#
# Usage: environment/create_frozen_env.sh [target-dir]   (default: .venv-frozen)
# Needs Python 3.12 (PYTHON overrides the interpreter) and network access to PyPI.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
target=${1:-.venv-frozen}
freeze="$here/audit-v2-pip-freeze.txt"
py=${PYTHON:-python3.12}

"$py" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 is required, found " + sys.version'
"$py" -m venv "$target"
# Every dependency is pinned in the freeze, so nothing outside it may be resolved.
"$target/bin/python" -m pip install --quiet --no-deps -r "$freeze"
"$target/bin/python" -m pip freeze | diff -u "$freeze" - && echo "pip freeze matches $(basename "$freeze")"
"$target/bin/python" "$here/check_frozen_env.py"
