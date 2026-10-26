# Verification record

This file separates tests actually recorded for the earlier submission from verification of the unified root application. Test results describe the tested configuration and revision; they do not establish an instructor's grade or acceptance.

## Current unified revision

**Passed on 26 October 2026, 18:12:36–18:13:10 UTC:** 44 application regression tests, real HTTPS checks, HTTP experiment restoration, runtime restrictions, and a bounded local request burst. The test containers and database volume were removed successfully.

The [machine-readable application record](verification/application.json) contains all tested file hashes, resolved Python packages and deployment checks. It was run from the working copy based on commit `b138325`, with source SHA-256 **`bf7d8b4a46ee79086f9ecd1f37b7bbf17aa8f9fc312e4b22019e4b70ecbf9638`**. That digest matches the current tested source; documentation-only changes after the run are outside the manifest.

| Verification | Result |
|---|---|
| Cryptography and passwords | AES-GCM nonce uniqueness, round trips, record binding and tamper rejection; atomic, repeatable comment migration; HMAC exact-byte verification; salted Argon2 and successful-login-only legacy upgrades |
| Identity and authorization | Forged/invalid/expired JWT rejection; live role and ownership enforcement; copied Cookie/JWT revocation after logout; new login credentials work |
| Requests and data | CSRF enforcement, escaped comments, CSV formula handling, enrollment/grade validation, safe argument-vector ping handling |
| Protected audit | Sensitive reads and change history recorded; application role cannot update/delete/truncate events; failed audit writes roll back grades, account creation and logout |
| Data bounds | Complete keyset pagination without cross-user disclosure; invalid cursors rejected; export limits reject incomplete files; oversized selectors rejected |
| Real deployment | Certificate-validated HTTPS, correct HTTP redirect, teacher login with Secure cookies, actual downloaded signed ZIP and tamper rejection; no direct app/DB ports, non-root app and non-privileged DB role |
| HTTP experiment | Actual plaintext-mode login works; returning to default Compose restores Secure cookies and removes the direct HTTP app port |
| Bounded availability check | 120 localhost requests with at most 12 concurrent: 38 returned 200 and 82 returned 429, no server errors; health returned 200 after two seconds |

The 44 tests ran in 10.071 seconds. No test failures or skips were reported. The page/API check inspects rendered HTML and makes actual Cookie-authenticated requests; it does not drive browser JavaScript. The ping regression mocks the subprocess to inspect arguments and timeout; it is not an ICMP/network penetration test.

Five additional [synthetic exercise tests](verification/exercises.json) passed. A separate [Python dependency audit](verification/python-dependencies.json), using pip-audit 2.10.1 and the PyPI advisory service in strict mode on 26 October, reported zero known vulnerabilities and zero skipped packages in the 15 resolved web packages and six exercise packages. This dependency check used host Python 3.13.16; it does not scan container OS packages or establish the absence of vulnerabilities.

Reproduction command, from the repository root with Docker, Python 3.9 or newer and OpenSSL installed:

```sh
python3 scripts/verify.py
```

The verifier creates an independent temporary Compose project, initializes its own database and secrets, runs the checks, and removes its test volumes afterward. It prints the result and writes `.verification/latest.json` (Git-ignored); use `--report PATH` to select a different location. The record captures the source revision/tree and working-copy digest so a result can be tied to its actual inputs.

A passing record does not apply automatically after its source files, dependency resolution, keys, data or deployment configuration change. The verifier uses invented test accounts and a fresh test database; existing student databases and private report files are not used or changed.

## Historical verification — 22 October 2026

Source: the clean-copy audit recorded in commit [`7c233be`](https://github.com/NoahLightryyy/NoteApp/commit/7c233be). This predates the unified application and must not be treated as its test result.

The earlier repository and packaging fixes were copied to a temporary directory without local secrets, existing volumes or untracked reports. Two isolated Compose projects were built. Test overlays changed host ports and removed root host mounts; application code, seeds and nginx configuration remained those of that submission.

| Earlier target | Recorded checks |
|---|---|
| Root Class 5 application | Fresh localhost certificate, verified TLS, HTTP redirect, teacher login, no published Flask port, password tests and rollback-only legacy-login upgrade |
| Separate C3/C4 application | Fresh independent keys and certificate, initialized database, comment encryption, repeatable migration, dashboard/API/teacher reads, inserts/updates, CSV/ZIP export, rejection of altered ciphertext, restored test records |
| HMAC | Both unit tests, modified-content rejection, ZIP download over verified TLS, signature validation |
| P1 documents | Original source references, 17 risk calculations, STRIDE coverage, flow numbering, links and diagram readability |

The original test record is preserved in Git. It used a separate C3/C4 implementation and therefore cannot prove that the current root application preserves those behaviors.

## Evidence limits

- The Class 5 findings reports were sent privately, according to the student's confirmation on 26 October. Their historical measurements and predictions are not replaced by these tests.
- Alice had already been migrated during earlier work. The earlier supplemental Alice test reenacted the plaintext-to-Argon2 transition inside a transaction that was rolled back; it did not recreate the historical first login. The current compatibility test entry point uses UUID-named fictional accounts in the disposable test database and never changes Alice.
- Existing reports describe their own dates and configurations. A later successful regression run does not retroactively establish an earlier submission date, prediction or classroom presentation.
