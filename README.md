# NotesApp

**Submission owner:** Lv Songyuan · **Student ID:** 2023901706

**P1 group:** Lv Songyuan (2023901706), Liu Yunfei (2023905324), Wu Siyuan (2023905932). This fork contains Lv Songyuan’s submission; the group has no separate repository.

Computer Security coursework: a Flask/PostgreSQL application for student grades and teacher comments. The current revision brings the C3, C4 and Class 5 implementations into the root application. [Verification results](VERIFICATION.md) distinguish the current revision from the earlier, separately tested applications.

## Coursework and submission

| Item | Where to review |
|---|---|
| P1 — threat model and risk analysis | [Report, diagrams, 17 scored STRIDE threats and Top 3 proposals](project1/README.md) · [requirement checklist](project1/SUBMISSION_CHECKLIST.md) |
| C3 — AES-GCM comments | [Encryption](web/comment_crypto.py) in the [root application](web/app.py): encrypted storage, authorized reads and comment migration |
| C4 — HMAC CSV export | [Signing and verification](web/csv_hmac.py) in the root application; altered exports must fail verification |
| C5a — HTTPS | Default [Compose configuration](docker-compose.yml) and [nginx configuration](nginx/nginx.conf) |
| C5b — Argon2 passwords | Root [login](web/app.py) and [password hashing](web/password_security.py); upgrade a legacy password after a successful login |

[Submission status](SUBMISSION_STATUS.md) records the requirement sources and delivery facts. The student confirmed privately sending the latest Lab 1 and Lab 2 reports, with both partners' names and IDs, to the instructor. Those reports are not republished here. P1 assesses the original course commit `1c83e42`; later implementation changes do not rewrite that historical assessment.

## Start the application

Prerequisites: Docker with Compose **2.24 or newer**, Python **3.9 or newer**, and OpenSSL available on the host. `curl` is optional for manual HTTP/TLS checks. Run commands from the repository root.

The optional [Session 03 image and password exercises](session03/README.md#standalone-synthetic-exercises-tasks-1-and-2) use Python **3.11+** and their own listed dependencies.

```sh
git clone https://github.com/NoahLightryyy/NoteApp.git notesapp
cd notesapp
python3 scripts/setup_local.py
docker compose up -d --build
```

Open **[https://localhost:8443](https://localhost:8443)**. The HTTP entry at [http://localhost:8081](http://localhost:8081) redirects to HTTPS. The default configuration does not publish Flask or PostgreSQL directly.

The generated localhost certificate is self-signed, so a browser trust warning is expected. Setup does not change the system trust store. TLS files stay in `nginx/certs/`; application and database secrets stay in `.secrets/`. Both directories are Git-ignored. Preserve the comment-encryption key together with the database: generating a replacement key cannot recover existing ciphertext.

The Compose project is `notesapp-coursework`, with a new independent database volume. Earlier `noteapp` and `notesapp-session03` volumes are preserved; starting this revision does not import their data. If an older application already uses ports 8443/8081, choose free ports instead of stopping it:

```sh
export NOTESAPP_HTTPS_PORT=9443 NOTESAPP_HTTP_PORT=9081
docker compose up -d --build
```

Then open `https://localhost:9443`. Keep the same environment values when rebuilding that deployment. For a manual TLS check, use its actual port:

```sh
curl --cacert nginx/certs/notesapp.crt "https://localhost:${NOTESAPP_HTTPS_PORT:-8443}/healthz"
```

| Role | Username | Demo password |
|---|---|---|
| Student | `alice` | `alicepw` |
| Teacher | `prof.turing` | `teach123` |
| Administrator | `admin` | `admin123` |

These are public course accounts for local exercises. The other seeded students use their username followed by `pw`.

**Log out all sessions** ends the account's sessions on every browser and invalidates its previously issued API tokens. Each subsequent authenticated request checks the account's current authentication version in PostgreSQL; logging in again creates credentials for the new version.

Grade and account lists use pages of 100 records. CSV exports accept up to 1,000 records and reject an oversized result instead of returning an incomplete file; use a course-specific export when needed. Course/student selectors accept up to 1,000 entries. These limits keep the classroom application bounded.

Sensitive reads and changes are recorded in the separate `notesapp_audit` database schema. The application can append events and read history, but cannot edit or delete existing events. Grade and account changes commit together with their audit record; an audit storage failure rejects the operation. The record contains actor, action, target, outcome and time, with grade changes but no passwords or comment text. Database administrators remain trusted; this local log is not an external archive.

## Verify a fresh deployment

```sh
python3 scripts/verify.py
```

The verifier uses an isolated temporary Compose project and test database, then cleans up its test volumes. It prints the result and saves a JSON record to the Git-ignored `.verification/latest.json`; `--report PATH` selects another report location. See [VERIFICATION.md](VERIFICATION.md) for the tested revision, results and limitations. A test pass does not establish instructor acceptance or the absence of every vulnerability; [SECURITY_STATUS.md](SECURITY_STATUS.md) tracks the security checks separately.

To verify a signed export downloaded from the teacher page, run the following command with the archive's actual location and the key belonging to that deployment:

```sh
python3 web/csv_hmac.py ~/Downloads/grades-signed.zip --key .secrets/csv_hmac.key
```

Trust the CSV only after `OK: CSV HMAC-SHA256 verified.` A changed CSV or a different deployment's key must fail verification. The key is local secret material; do not include it in a submission or share it with the export.

## HTTP capture exercise

Use this only when reproducing the Class 5 plaintext-traffic comparison:

```sh
docker compose -f docker-compose.yml -f docker-compose.http-lab.yml up -d --build
```

The experiment enables **[http://localhost:8080](http://localhost:8080)** on loopback. HTTPS on port 8443 remains available, but the experiment also exposes a plaintext path; it must not be described as an HTTPS-only deployment.

After the capture, restore the default configuration:

```sh
docker compose up -d --build
```

## Update, stop and existing data

To update and rebuild the default HTTPS deployment:

```sh
git pull
python3 scripts/setup_local.py
docker compose up -d --build
```

To stop it while retaining the database and local keys:

```sh
docker compose down
```

Do not delete an old database volume or encryption key to perform an upgrade. This revision starts a new course database and does not merge or migrate the two older deployments. Reusing their data requires a separately agreed backup and import procedure that preserves the corresponding comment key. No automatic adoption command is provided here.

The old `session03/task3_notesapp` path is retained as a compatibility entry point for the root application, rather than a second application implementation. See [Session 03 notes](session03/README.md). Earlier code and experiment history remain available in Git.
