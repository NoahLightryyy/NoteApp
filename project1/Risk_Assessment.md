# NotesApp risk assessment

Group review version, 15 October 2026. Based on the group’s TH01–TH17 register. Scores assume the unchanged teaching application is reachable by untrusted network clients and its published default configuration is known. These are analytical estimates, not new attack-test results.

## Risk scoring method

Risk = likelihood × impact, using ordinal scores from 1 to 5. Multiplication supports prioritization, not a numerical probability or expected financial loss. Related threats and attack chains are not added together.

| Score | Likelihood in the stated deployment | Impact if the scenario succeeds |
|---|---|---|
| 1 | Exceptional prerequisites; largely theoretical | Negligible, readily reversible effect |
| 2 | Several uncommon conditions or user-dependent steps | Limited effect on one noncritical function |
| 3 | Credible but needs privilege, access, victim behavior or uncertain capacity | Material effect on a limited set of records or accountability |
| 4 | Straightforward for an ordinary authenticated actor | Broad grade disclosure/tampering or service-wide interruption |
| 5 | Directly exposed, low-complexity path without an account | Administrative, credential-wide or runtime/host compromise |

Bands: 1–4 Low; 5–9 Moderate; 10–16 High; 17–25 Critical. These scales and bands are assessment choices, not values prescribed by the assignment.

## STRIDE register and ratings

S = Spoofing; T = Tampering; R = Repudiation; I = Information disclosure; D = Denial of service; E = Elevation of privilege. A threat may affect multiple categories. Same-role access to another user's resources is described explicitly; an E label here includes exceeding the intended authorization scope, not necessarily changing the stored role.

| Threat | STRIDE | Scope | L | I | Risk | Level |
|---|---|---|---:|---:|---:|---|
| TH01 | S T E | F01–F04 / TB1 TB2 | 5 | 5 | 25 | Critical |
| TH02 | S E | F04 and session-protected routes / TB1 | 5 | 5 | 25 | Critical |
| TH03 | S I | F13–F16 / TB1 | 5 | 4 | 20 | Critical |
| TH04 | I | F13–F16 / TB1 TB2 | 5 | 4 | 20 | Critical |
| TH05 | I E | F17–F20 F25–F28 / TB1 TB2 | 4 | 4 | 16 | High |
| TH06 | T E | F21–F24 / TB1 TB2 | 4 | 4 | 16 | High |
| TH07 | T I | F21–F24 then F09–F12 or F17–F20 / TB1 TB2 | 3 | 4 | 12 | High |
| TH08 | T E | F07–F08 F21–F24 F33–F40 / TB1 | 3 | 4 | 12 | High |
| TH09 | S T I | TB1 / HTTP deployment | 3 | 5 | 15 | High |
| TH10 | I | PostgreSQL and container backups / TB2 TB4 TB5 | 3 | 5 | 15 | High |
| TH11 | R | F01–F40 F51–F52 / logging | 4 | 3 | 12 | High |
| TH12 | D | HTTP routes and F51–F52 | 3 | 4 | 12 | High |
| TH13 | T D E | F37–F40 / TB1 TB3 | 3 | 5 | 15 | High |
| TH14 | E | F38 F53–F56 / TB4 | 3 | 5 | 15 | High |
| TH15 | T I | F21–F28 / TB6 | 2 | 4 | 8 | Moderate |
| TH16 | T | F21–F24 / TB2 | 4 | 3 | 12 | High |
| TH17 | S I | F04 F07–F08 F12–F16 / TB1 | 3 | 4 | 12 | High |

### TH01

Concatenated login SQL allows attacker-controlled credentials to change query logic and potentially authenticate as another user.

**Evidence:** `web/app.py:142–174, login`.

**Likelihood 5:** Unauthenticated input reaches SQL directly; the source is available. **Impact 5:** An administrative identity enables broad account and grade operations.

**Mitigation:** Use bound SQL parameters, generic failures, least-privilege DB access and modern password hashing.

### TH02

The published Flask signing secret permits creation of accepted session data, including a privileged role.

**Evidence:** `web/app.py:29–33,119–125; docker-compose.yml:27`.

**Likelihood 5:** The configured secret is present in the supplied source; no prior account is required. **Impact 5:** A forged administrator session exposes all administrative actions.

**Mitigation:** Replace and rotate the secret outside Git, invalidate old sessions, and check current roles against trusted server-side records.

### TH03

The API accepts unsigned JWTs and a weak published HMAC key, allowing a forged Bearer identity to pass its authentication check.

**Evidence:** `web/app.py:67–115,202–222`.

**Likelihood 5:** An unsigned-token branch accepts a payload without verifying a signature. **Impact 4:** All grade records may be disclosed through the API; this path does not authenticate browser admin pages.

**Mitigation:** Use a maintained JWT library, pin the allowed algorithm, reject unsigned tokens, protect keys and validate identity and claims; enforce note ownership separately.

### TH04

A logged-in student can request another student’s note because the API selects by record ID without checking ownership.

**Evidence:** `web/app.py:202–222; student observation reported in conversation`.

**Likelihood 5:** Changing a note ID is simple for any student; earlier student observation reports cross-user reads. **Impact 4:** Grades and private comments across students can be disclosed.

**Mitigation:** Scope queries to the current student; define explicit teacher/admin policies and test the permission matrix.

### TH05

A teacher can view or export classes assigned to other teachers because class ownership does not restrict the queries.

**Evidence:** `web/app.py:226–244,276–306; README role policy`.

**Likelihood 4:** An ordinary teacher account can use the normal page or export endpoint. **Impact 4:** Bulk disclosure extends beyond the teacher’s assigned classes.

**Mitigation:** Filter classes and exports by the authenticated teacher ID; reject unauthorized class IDs.

### TH06

A teacher can create or update grades in another teacher’s class when the route checks the teacher role but not class ownership.

**Evidence:** `web/app.py:248–272`.

**Likelihood 4:** Teacher credentials and a chosen record/class ID are sufficient prerequisites in the code. **Impact 4:** Unauthorized changes undermine academic records across classes.

**Mitigation:** Verify class ownership and enrollment in the write transaction; constrain updates by both record and authorized class.

### TH07

An actor allowed to write a comment can store active HTML/script that is rendered without escaping to another user.

**Evidence:** `web/templates/dashboard.html:15; web/templates/teacher.html:47`.

**Likelihood 3:** Requires comment-write access and a victim viewing the stored content. **Impact 4:** Script can alter displayed data and act in the victim browser; HttpOnly does not stop same-origin actions.

**Mitigation:** Restore autoescaping; if rich text is necessary apply a strict sanitizer, and add CSP as defense in depth.

### TH08

Missing CSRF validation can allow unwanted state changes when a victim browser sends a session cookie with an attacker-induced request.

**Evidence:** `web/app.py:179–181,248–272,325–341,363–379; no CSRF integration`.

**Likelihood 3:** Requires a logged-in victim and a request context where browser cookie rules permit the cookie. **Impact 4:** Teacher or admin actions could be induced; ping consequences may chain to TH13.

**Mitigation:** Add server-validated CSRF tokens to mutations, use POST logout, check origins and set SameSite explicitly.

### TH09

On an accessible untrusted network, plaintext HTTP can expose credentials/session cookies and allow response or request modification.

**Evidence:** `docker-compose.yml:29–30; web/app.py:392–394; recorded HTTP observation`.

**Likelihood 3:** Requires network positioning; the observed loopback capture does not establish interception. **Impact 5:** A stolen privileged session can compromise administrative operations.

**Mitigation:** Deploy HTTPS, set Secure and HttpOnly cookies, choose SameSite, and restrict development bindings to loopback.

### TH10

Database access exposes plaintext passwords/comments; container-image access also exposes a baked password backup.

**Evidence:** `db/init.sql:8–35; web/Dockerfile:17–23; docker-compose.yml:11–12`.

**Likelihood 3:** Requires database, image, backup or filesystem access; published database settings broaden exposure if reachable. **Impact 5:** Credential disclosure enables account compromise and reveals private records.

**Mitigation:** Hash passwords with Argon2id or another suitable password KDF; encrypt sensitive comments with separately managed keys; remove baked secrets/backups and restrict DB access.

### TH11

Incomplete, locally writable audit records leave insufficient evidence to attribute or reconstruct reads and administrative changes.

**Evidence:** `web/app.py:38–44,170–175,271,339; web/Dockerfile:22–23`.

**Likelihood 4:** Normal sensitive operations omit key audit fields; code can silently ignore logging failures. **Impact 3:** Disputes and incident reconstruction become difficult even when data is still available.

**Mitigation:** Record actor, action, target, outcome and time; capture protected change history, centralize append-only logs, and alert on failures.

### TH12

Unbounded result sets, no application rate limiting and growing logs may exhaust database, worker or disk resources.

**Evidence:** `web/app.py:38–44,226–244,276–306; Compose has no resource limits`.

**Likelihood 3:** Repeated traffic is possible, but practical thresholds depend on host resources and middleware. **Impact 4:** Service-wide unavailability could block grade access and updates.

**Mitigation:** Add rate limits, pagination, request-size limits, timeouts, log rotation and container quotas; validate with a bounded authorized load test.

### TH13

The administrator-controlled host string is concatenated into a shell command, enabling command execution beyond the intended ping function.

**Evidence:** `web/app.py:325–341; web/Dockerfile:24`.

**Likelihood 3:** Requires an administrator session, possibly obtained through TH01 or TH02. **Impact 5:** Commands run with the web process privileges and can damage the service or lead to TH14.

**Mitigation:** Avoid shell=True, validate destinations, use fixed executable arguments, restrict egress, and run the process with minimal privileges.

### TH14

Code execution in a root web container may allow control of the Docker Engine through the mounted socket and modification of bind-mounted project files.

**Evidence:** `docker-compose.yml:35–37; web/Dockerfile:24`.

**Likelihood 3:** Requires code execution and usable socket permissions; root alone is not a container escape. **Impact 5:** Compromise can extend to the Docker Engine host and other workloads.

**Mitigation:** Remove the Docker socket and broad host mount, use a non-root user and read-only filesystem, drop capabilities and isolate the runtime.

### TH15

An attacker-written comment exported as CSV may be treated as a formula by a spreadsheet application.

**Evidence:** `web/app.py:298–305; OWASP CSV Injection`.

**Likelihood 2:** Requires a writable comment, teacher download and spreadsheet behavior/settings that evaluate the cell. **Impact 4:** Spreadsheet content or accessible information may be affected; exfiltration depends on application controls.

**Mitigation:** Export untrusted cells as explicit text using a tested spreadsheet-safe policy; quoting CSV alone does not neutralize formulas.

### TH16

The grade route does not enforce a business grade range or verify that the selected user is an enrolled student in the class.

**Evidence:** `web/app.py:248–268; db/init.sql notes/enrollments definitions`.

**Likelihood 4:** A teacher can submit values directly; foreign keys do not enforce role, enrollment or grade policy. **Impact 3:** False academic records or out-of-policy grades can be stored.

**Mitigation:** Agree the allowed grade range, validate role/enrollment and numeric input, then enforce appropriate database constraints.

### TH17

Issued JWTs lack expiry and copied tokens can still be used at the API after logout clears the browser session.

**Evidence:** `web/app.py:67–102,167–169,179–181,202–207`.

**Likelihood 3:** Requires a previously copied token; logout does not implement token revocation. **Impact 4:** Grade access may persist beyond the intended session.

**Mitigation:** Require expiry and issuer/audience validation, short lifetimes and a revocation/version mechanism; revoke on logout when policy requires it.

## Review and attribution

AI assisted with code review, organization, proposed ratings and English wording. Group members should confirm the scenario, scores and mitigations under the course AI policy. Source paths are relative to the NotesApp repository; the full package includes the diagram mapping and source register. CSRF, CSV formula evaluation, denial-of-service thresholds and host consequences remain conditional rather than demonstrated.
