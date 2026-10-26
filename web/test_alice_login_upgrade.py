"""Supplemental isolated reenactment, not historical Alice migration evidence.

This historical command now exercises the same legacy-password scenario on
UUID-named fictional users in the disposable test stack. It never changes Alice
or relies on her password. Run python3 scripts/verify.py from the repository root.
"""
from pathlib import Path
import sys

for root in (Path(__file__).resolve().parent, Path(__file__).resolve().parents[1]):
    if (root / "tests" / "legacy_runner.py").is_file():
        sys.path.insert(0, str(root))
        break

from tests.legacy_runner import run

if __name__ == "__main__":
    run("tests.test_security.LoginUpgradeTests.test_legacy_wrong_password_does_not_migrate_success_does")
