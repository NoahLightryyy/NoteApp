# NotesApp top three risks and fixes

Group review version, 15 October 2026. Based on the group’s TH01–TH17 register. Scores assume the unchanged teaching application is reachable by untrusted network clients and its published default configuration is known. These are analytical estimates, not new attack-test results.

Risk = likelihood × impact, each rated 1–5. The full scale, all 17 ratings and their rationales are in the companion file Risk_Assessment.md.

## The three highest priority risks

TH01 and TH02 both score 25. TH03 and TH04 both score 20; TH03 is selected third because it removes the need for an existing student session. TH04 remains an urgent independent authorization defect even after JWT verification is fixed.

### Priority 1 TH01 Login SQL injection

**Risk 25.** Unauthenticated credential input is concatenated into a SQL query. A changed query may produce another user's identity and administrative access.

**Fix:** use parameterized database queries and a dedicated password-hash verification step; restrict the database account's privileges and avoid exposing raw database errors. Password hashing alone does not fix injection, and rate limiting alone does not remove it.

**Acceptance checks:** valid credentials still work; incorrect credentials fail; quotes and SQL-like strings are treated strictly as values; no rejected login creates a session or exposes database error details. Review the query construction in code as well as testing outcomes.

### Priority 2 TH02 Published session signing secret

**Risk 25.** The application trusts session identity and role fields signed with a secret distributed in the project configuration. Anyone knowing that secret may create accepted session data without possessing a user's password.

**Fix:** generate a strong deployment-specific secret outside source control, rotate the exposed secret and invalidate old sessions. Resolve sensitive roles from trusted server-side state and enforce authorization at every operation. Protect transport and cookies as additional controls.

**Acceptance checks:** new legitimate sessions work; sessions signed with the old secret fail; modified role data fails; revoked accounts and role changes take effect on protected endpoints. Check repository, image and logs for leaked replacement secrets without publishing them.

### Priority 3 TH03 Forged API tokens

**Risk 20.** The custom verifier accepts `alg: none` and uses a published weak HMAC key. A forged Bearer token can pass the API identity gate. This is not evidence that browser-only teacher/admin routes accept that token.

**Fix:** replace the custom verifier with a maintained library, allow only the selected signed algorithm, protect and rotate keys, require expiry and intended issuer/audience, and resolve a valid current identity. Independently enforce ownership on `/api/notes/<id>` to fix TH04; correct token verification alone is insufficient.

**Acceptance checks:** unsigned, wrong-key, malformed and expired tokens return 401; a valid student token can read an allowed record but not another student's record; invalid-token failures do not return server errors or leak grades. Test cookie-authenticated API access too.

### Attack chain and parallel containment

TH01 or TH02 may provide the administrator session needed for TH13. Shell execution can then expose TH14 through the Docker socket. Keep TH13 and TH14 as separate findings with their own prerequisites; do not treat them as independently unauthenticated paths or add their scores. Remove the socket and shell interpretation promptly even though they are not among the three largest individual scores.


## Review and attribution

AI assisted with code review, organization, proposed ratings and English wording. Group members should confirm the scenario, scores and mitigations under the course AI policy. Source paths are relative to the NotesApp repository; the full package includes the diagram mapping and source register. CSRF, CSV formula evaluation, denial-of-service thresholds and host consequences remain conditional rather than demonstrated.
