"""Compatibility entry point for the root localhost certificate generator."""
from pathlib import Path
import runpy
root = Path(__file__).resolve().parents[2]
runpy.run_path(str(root / 'nginx/create_tls_cert.py'), run_name='__main__')
