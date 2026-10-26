"""Compatibility entry point for isolated password and account regressions.

Run python3 scripts/verify.py from the repository root. No fixed seed credentials
or IDs are used, and tests refuse the existing coursework database.
"""
from pathlib import Path
import sys

for root in (Path(__file__).resolve().parent, Path(__file__).resolve().parents[1]):
    if (root / "tests" / "legacy_runner.py").is_file():
        sys.path.insert(0, str(root))
        break

from tests.legacy_runner import run

if __name__ == "__main__":
    run("tests.test_crypto.CsvAuthenticationTests.test_independent_random_password_salts",
        "tests.test_security.LoginUpgradeTests",
        "tests.test_security.ValidationAndAdminTests")
