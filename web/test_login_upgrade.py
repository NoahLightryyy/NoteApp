"""Compatibility entry point for isolated login migration regressions.

Run python3 scripts/verify.py from the repository root. The suite uses unique
fictional accounts in a dedicated test database and does not touch real users.
"""
from pathlib import Path
import sys

for root in (Path(__file__).resolve().parent, Path(__file__).resolve().parents[1]):
    if (root / "tests" / "legacy_runner.py").is_file():
        sys.path.insert(0, str(root))
        break

from tests.legacy_runner import run

if __name__ == "__main__":
    run("tests.test_security.LoginUpgradeTests")
