"""Test configuration for the CPU-only evidence-remediation suite."""

from pathlib import Path
import sys


NEW_WORK_ROOT = Path(__file__).resolve().parents[1]
if str(NEW_WORK_ROOT) not in sys.path:
    sys.path.insert(0, str(NEW_WORK_ROOT))
