"""Compatibility entry point for the unified local setup."""
from pathlib import Path
import runpy
import sys
root = Path(__file__).resolve().parents[2]
sys.argv = [str(root / 'scripts/setup_local.py')]
runpy.run_path(sys.argv[0], run_name='__main__')
