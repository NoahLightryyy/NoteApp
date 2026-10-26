"""Keep historical test entry points usable without touching the live database."""
import os
import unittest


def run(*names):
    if (os.environ.get("NOTESAPP_TEST_DATABASE") != "1"
            or os.environ.get("DB_NAME") != "notesapp_test"):
        raise SystemExit(
            "This historical entry point now uses disposable UUID fixtures only. "
            "Run python3 scripts/verify.py from the repository root to build and "
            "check an isolated database; the existing coursework database is not modified."
        )
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
