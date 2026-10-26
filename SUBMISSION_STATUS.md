# Coursework submission audit

Reviewed on **22 October 2026** for **Lv Songyuan (2023901706)**. This records verifiable contents and delivery information, not a grade or instructor acceptance.

Delivery clarification on **26 October 2026**: the student confirmed that the privately sent attachments were the latest Lab 1 / Lab 2 reports or ZIP, containing both partners' names and student IDs.

## Requirements and evidence

| Item | Requirement source | Evidence in this submission | Delivery status |
|---|---|---|---|
| P1 | Original Session 03 slide 31/32: diagram with trust boundaries; each STRIDE category; likelihood × impact per threat; Top 3 with fixes | [Full report](project1/README.md), diagrams, 17 scored threats, synchronized extracts | GitHub; formal group/deadline caveats in [P1 checklist](project1/SUBMISSION_CHECKLIST.md) |
| C3 | Original Session 03 slide 30: encrypt the comment column with AES-GCM; fresh nonce guidance on slide 32 | [AES-GCM](session03/task3_notesapp/web/comment_crypto.py), [migration](session03/task3_notesapp/web/migrate_comments.py), [read/write verification](session03/task3_notesapp/test_routes.py) | GitHub, in the separate combined lab |
| C4 | Teacher's class-5 audit column: HMAC-signed CSV export; student's explicit HMAC request | [HMAC-SHA256 and local verifier](session03/task3_notesapp/web/csv_hmac.py), [tests](session03/task3_notesapp/test_csv_hmac.py) | GitHub; a more detailed original C4 rubric was not present in the material recovered for this review |
| C5a / Lab 1 | [Official HTTPS lab](https://kristenpire.github.io/epita-security-labs/class5/https-lab/): findings sheet with HTTP exposure, HTTPS recapture and certificate-trust comparison; working nginx HTTPS | Root [overlay](docker-compose.https.yml), [nginx](nginx/nginx.conf), [certificate generator](nginx/create_tls_cert.py); local report contains both findings and six supporting images | Report privately sent to instructor, confirmed by student; reproducible code in GitHub |
| C5b / Lab 2 | [Official password audit](https://kristenpire.github.io/epita-security-labs/class5/password-audit/): findings sheet for wordlist attack, timing, held-out accounts, Argon2 comparison and verdict; legacy login upgrade | [Root login](web/app.py), [hashing](web/password_security.py), [rollback upgrade test](web/test_login_upgrade.py), [Alice supplemental test](web/test_alice_login_upgrade.py) | Report privately sent to instructor, confirmed by student; code and tests in GitHub |

The official Class 5 hand-in is the findings sheet; implementation code supports the experiment. The reports are not republished here because the student has already delivered them directly. Receipt or grading by the instructor has not been independently verified.

## Checked in a clean copy

The repository contents plus this audit's packaging fixes were copied into a separate temporary directory, without local secrets, existing database volumes or untracked reports. Two isolated Docker Compose projects were built from that copy. Test-only overlays used alternate host ports and removed root host mounts to avoid touching the student's live application; application source, database seeds and nginx configurations remained those of the submission.

- Root: generated fresh localhost certificate; validated TLS; HTTP redirected to HTTPS; teacher login succeeded; Flask had no published host port; password and rollback login-upgrade tests passed.
- Combined C3/C4 lab: generated fresh independent keys and certificate; initialized a new database; encrypted comments; verified migration repeatability, dashboard/API/teacher reads, insert/update, CSV/ZIP exports and rejection of altered ciphertext; test records restored.
- HMAC: both unit tests passed, including modified-content rejection; signed ZIP downloaded over verified TLS and its signature validated.
- P1: source baseline references, 17 risk calculations, category coverage, flow numbering, local links and diagram readability checked. F61/F62 table formatting corrected.
- Generated certificates, keys, captures, test database volumes and unrelated exercises are excluded from the Git commit.

## Differences that must not be misrepresented

1. **Alice's migration history.** Earlier work had already migrated the live Alice account. The submitted Lab 2 report says so; her later successful logins do not establish a first-login plaintext-to-hash transition. A separate rollback-only test now demonstrates that transition using Alice in an isolated transaction and restores her original stored value. This is supplemental verification, not a rewrite of the historical experiment.
2. **SQL injection scaffold.** The Lab 2 scaffold asks students to retain username SQL concatenation for a later class. This fork had already repaired login SQL injection in an earlier exercise, and retains bound SQL parameters. Argon2 migration is implemented, but this is an explicit additional hardening difference from that scaffold.
3. **Separate deployments.** C3/C4 are implemented in `session03/task3_notesapp`; C5b upgrade-on-login is implemented in root `web/`. The combined copy retains its older startup bulk-migration behavior. The [README submission map](README.md#submission-map) gives each entry point rather than claiming that root startup enables every lab.
4. **Report identity and version.** Reviewed local reports use “Lyu Songyuan” with the same student ID, while this repository follows the student's requested “Lv Songyuan”. On 26 October, the student confirmed sending the latest Lab 1 / Lab 2 reports or ZIP, which include both partners' names and student IDs. The older bundle's missing partner/ID line does not apply to the confirmed submission.
5. **Historical prediction.** The Lab 2 report records the pre-attack time prediction but states that the predicted number of cracked accounts was not recorded. No retrospective prediction has been invented.
6. **P1 formalities.** This fork first received P1 on 22 October, after the original 20 October deadline. An earlier group hand-in or extension has not been verified. Other P1 members and the designated group repository are not established by the reviewed records. The student has deferred the presentation; this is not documented instructor exemption.
