# Security verification status

The [P1 report](project1/README.md) models the original teaching application at `1c83e422429c4b784411701ffd797b5ab5f397dc`. Its risk scores and proposed fixes remain an assessment of that version.

The current revision consolidates the application and adds security changes. **The 44 application regression tests and isolated deployment checks passed on 26 October 2026.** The exact tested source, recorded results and limits are in [VERIFICATION.md](VERIFICATION.md) and the [machine-readable record](verification/application.json). This verifies the listed checks, not the absence of every possible vulnerability.

| Area | Verified behavior | Current evidence status |
|---|---|---|
| Login and passwords | Bound SQL parameters; reject wrong credentials; salted Argon2 storage; upgrade legacy values only after successful login | Passed; synthetic accounts in an isolated DB |
| Session and API identity | Protect signing material; reject unsigned, malformed, wrong-key and expired tokens; enforce current identity and role; reject copied cookies and API tokens after logout of all sessions | Passed; actual Cookie/JWT replay regressions |
| Record permissions | Students access their own records; teachers read/export/write only permitted classes; unauthorized requests do not disclose or modify grades | Passed; cross-account/class regressions |
| Comments | Encrypt storage using AES-GCM with fresh nonces; retain readable data during migration; reject tampering; escape displayed user input | Passed; storage, migration, API and rendered HTML checks |
| Requests and command execution | Validate state-changing requests; prevent shell interpretation of the ping destination; validate grade and enrollment rules | Passed; ping subprocess arguments were mocked and inspected |
| CSV export | Verify HMAC over exact bytes; reject modified exports; enforce teacher scope; handle untrusted spreadsheet cells | Passed; unit/route checks plus real HTTPS ZIP download |
| Audit history | Persist sensitive reads and transaction-linked changes; prevent application edits/deletes; roll back when audit storage fails | Passed; audit DB permission and failure regressions |
| Data bounds | Paginate scoped lists; reject oversized exports/selectors without silent truncation | Passed; real fixture rows with small boundary limits |
| Transport and runtime | Default HTTPS with redirect; no direct app/database ports; no Docker socket or broad host mounts; restricted process privileges | Passed; configuration review and real isolated runtime checks |

## Mapping to the original P1 threats

This maps the original threats to current controls without changing the historical P1 scores. The audit-history and bounded availability checks passed in the final run. The evidence applies to this local configuration; it does not mean every attack or deployment has been tested.

| P1 threat | Current control and remaining boundary |
|---|---|
| TH01 — login SQL injection | Login uses bound parameters, generic failures and Argon2 verification. The application DB role has no superuser, database-creation or role-creation privileges. |
| TH02 — published session secret | Setup generates a separate random signing key outside Git. Each request resolves the current account and role from PostgreSQL and checks the session's authentication version. Deployment owners still manage key backup and rotation. |
| TH03 — forged API tokens | PyJWT accepts HS256 only and requires subject, issuer, audience, issue time, expiry and a valid authentication version. Replacement signing material is generated locally. |
| TH04 — student record access | API and browser queries restrict students to their own notes; teacher and administrator access follows explicit role policies. |
| TH05 — teacher disclosure/export | Teacher lists and CSV/ZIP exports filter by the teacher's assigned classes; a requested class must also be authorized. |
| TH06 — cross-class grade changes | Grade writes check class ownership, student role and enrollment in the write transaction; updates retain the note's original student and class. |
| TH07 — stored script execution | Templates escape comments, browser API output uses `textContent`, and CSP restricts scripts. This does not provide a rich-text editor or sanitizer. |
| TH08 — forged browser mutations | All mutations require a session-bound CSRF token; logout uses POST and cookies use SameSite=Lax. Separate Origin/Referer filtering is not configured; the CSRF token is the primary request check. |
| TH09 — plaintext transport | Default entry points are loopback HTTPS and an HTTP redirect, with Secure/HttpOnly cookies and no direct Flask port. The certificate is self-signed; the explicit HTTP capture mode intentionally reintroduces plaintext and is outside this default claim. |
| TH10 — plaintext data/backups | Seeds and new passwords use Argon2id; correct legacy logins upgrade their stored values. Comments migrate to AES-GCM before serving, using a key outside PostgreSQL. The image no longer contains the old password backup. Public demo passwords remain intentional, and older volumes/images are not retroactively sanitized. |
| TH11 — incomplete or mutable audit history | Sensitive reads record actor/action/target/outcome/time. Grade, account, password-upgrade and logout changes record protected history in the same transaction. The application can append through a fixed function and read the audit table, but cannot update, delete or truncate it. Audit failures are visible on stderr and fail the request; rollback and permission regressions passed. |
| TH12 — resource exhaustion | nginx/login rate limits, request-size limits, DB/worker timeouts, container CPU/memory/PID limits and Docker log rotation are configured. Grade lists and administrator lists use ID cursors with 100 rows per page; exports reject more than 1,000 rows with 413, and teacher selectors have a 1,000-row bound. Comment migration streams batches of 100. A bounded 120-request/12-worker burst returned 38 HTTP 200 and 82 HTTP 429 responses, no server errors, and recovered after two seconds. These checks do not establish production capacity or protection from every denial-of-service pattern. |
| TH13 — shell command injection | Ping uses fixed arguments without a shell, accepts only loopback destinations and has a timeout. The default web container is non-root and connects only to the internal backend network. |
| TH14 — Docker/host control | The default web container has no Docker socket or broad project/host mount; its filesystem is read-only, capabilities are dropped and privilege escalation is disabled. Specific DB initialization files and nginx configuration/certificates remain mounted read-only. The Docker host and its administrators remain trusted. |
| TH15 — spreadsheet formulas | Untrusted cells with formula/control prefixes are exported as text, and HMAC authenticates the exact CSV bytes. Regression tests inspect exported bytes; behavior in every spreadsheet product/import mode has not been established. |
| TH16 — invalid academic records | The application requires grades from 0 to 20 with at most one decimal place and checks the student/enrollment. The DB also checks the grade range and foreign keys; role/enrollment policy is enforced by the application transaction rather than a DB trigger. |
| TH17 — credential replay after logout | Tokens expire after 15 minutes. “Log out all sessions” advances the account's DB authentication version, so subsequent requests reject old cookies and API tokens. Browser grade-detail requests use the current cookie instead of a token frozen when the page loaded. |

## Scope limits

Demo credentials remain public because this is a local course exercise. The local certificate is self-signed. The opt-in HTTP capture configuration deliberately exposes plaintext traffic on loopback. Results for the default HTTPS configuration do not apply unchanged to that experiment.

Login throttling is process-local and resets when the application restarts. With the current reverse proxy, requests share its address and therefore its 30-attempt, five-minute IP budget; each username also has a 10-attempt budget. Successful logins count toward these budgets. This bounds local authentication work but is not a distributed or per-browser rate-limit service.

Audit history is protected against modification by the application DB role. It is not an external immutable archive: the database owner and host administrator retain management access. External alert delivery, audit backup/retention policy and production capacity monitoring remain deployment responsibilities.

Regression checks are bounded functional evidence. They are not a penetration test, exhaustive denial-of-service assessment, external security certification or production deployment approval. Changes to the code, dependency versions, keys, data or deployment can change the outcome.
