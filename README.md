# NotesApp

## Student information

- Name: Lv Songyuan
- Student ID: 2023901706

A small grades application used throughout the Computer Security course. Teachers
record grades and comments for their classes, students read their own grades, and an
admin manages users and classes.

## Run it

You need Docker with the Compose plugin.

```
git clone git@github.com:KristenPire/NoteApp.git notesapp
cd notesapp
docker compose up
```

The first start builds the image, launches PostgreSQL, and loads the seed data
automatically. When it is ready, open:

```
http://localhost:8080
```

## Test accounts

| Role    | Username      | Password   |
|---------|---------------|------------|
| Student | `alice`       | `alicepw`  |
| Teacher | `prof.turing` | `teach123` |
| Admin   | `admin`       | `admin123` |

(There are ~30 students in total; each student's password is their username + `pw`,
e.g. `bob` / `bobpw`.)

## Stack

- Python 3.11 + Flask (server-rendered Jinja2 pages and a small JSON API)
- PostgreSQL 15
- Docker Compose (`web` and `db` services)

## Reset

```
docker compose down -v   # wipes the database volume
docker compose up        # reloads the seed data
```

## Updating your fork

The course repository is sometimes updated. Your fork does **not** update by itself.
To pull the latest changes into your fork:

**Easiest (GitHub website):** open your fork, and if it says *"This branch is behind
KristenPire/NoteApp"*, click **Sync fork → Update branch**. Then, in your local clone:

```
git pull
```

**Command line (keeps your own commits):**

```
git remote add upstream https://github.com/KristenPire/NoteApp.git   # once
git fetch upstream
git merge upstream/main
git push
```

Then **rebuild**, because the app code is baked into the Docker image:

```
docker compose up --build
```

A plain `docker compose up` would keep running the old image.

## Session 03: authenticated CSV exports

The encrypted-comments version in `session03/task3_notesapp` exports CSV with
HMAC-SHA256 authentication. HMAC detects changes; it does not encrypt the CSV.
The teacher's export link downloads `grades.zip`, containing `grades.csv` and
`grades.csv.hmac`. The signature covers the exact UTF-8 CSV bytes, including
line endings. Opening and saving the CSV in a spreadsheet may invalidate it.

Create the independent 32-byte HMAC key (existing keys are preserved), then rebuild:

```sh
python3 session03/task3_notesapp/create_key.py
python3 session03/task3_notesapp/create_tls_cert.py
docker compose -f session03/task3_notesapp/compose.yaml up -d --build
```

Verify a downloaded ZIP locally, without extra Python dependencies:

```sh
python3 session03/task3_notesapp/web/csv_hmac.py ~/Downloads/grades.zip --key session03/task3_notesapp/secrets/csv_hmac.key
```

Verification exits with status 0 on success and 1 on failure. Keep the key private
and backed up; anyone with the key can also create valid signatures. The key is
mounted as a Docker secret and is never included in the export. Retain the old key
if you rotate it and need to verify old exports.

Direct `/export.csv` requests still return CSV, with a hexadecimal signature in
`X-CSV-HMAC-SHA256`. Add `signed=1` to download the ZIP with its signature file.

Run the standalone signature tests:

```sh
python3 -m unittest discover -s session03/task3_notesapp -p test_csv_hmac.py
```

### Session 03 HTTPS

Open https://localhost:8443. The old http://localhost:8081 address redirects to
HTTPS. Nginx accepts TLS 1.2/1.3; Flask has no published host port and its session
cookie uses Secure, HttpOnly and SameSite=Lax. HMAC exports work over HTTPS.

The generated localhost certificate is self-signed: browsers will report it as
untrusted until you explicitly trust this local certificate. The setup does not
modify your system trust store. For a public deployment, replace it with a
trusted certificate for your domain and update the nginx hostname and redirect.
This remains a teaching app with other deliberately insecure features.

Check TLS with the generated certificate (without disabling verification):

```sh
curl --cacert session03/task3_notesapp/secrets/tls/localhost.crt https://localhost:8443/healthz
```

TLS configuration reference: https://nginx.org/en/docs/http/configuring_https_servers.html

## Coursework submissions

- **P1:** [Threat model, diagrams, STRIDE analysis and Top 3 fixes](project1/README.md), submitted by Lv Songyuan (2023901706). The report assesses the original course commit, before these lab fixes.
- **C3 / C4 / C5a:** Comment encryption, HMAC CSV exports and nginx HTTPS are in `session03/task3_notesapp` (instructions above).
- **C5b:** Both `web/` and `session03/task3_notesapp/web/` use Argon2id for passwords. Login fetches the username with a bound SQL parameter, verifies its hash, and refreshes outdated hash parameters after a successful login. Admin-created users and database seeds store salted hashes.

Argon2id uses 64 MiB memory, 3 iterations, 4 lanes and a fresh random salt per password, via [argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/api.html). Passwords are hashed, not reversibly encrypted. The documented demo credentials still work.

Rebuild either application to install the dependency. Before serving requests, its startup atomically migrates any existing plaintext passwords in the database; reruns preserve existing hashes. Do not delete the data volume to upgrade. For the combined HTTPS lab:

```sh
docker compose -f session03/task3_notesapp/compose.yaml up -d --build
docker compose -f session03/task3_notesapp/compose.yaml exec -T web python test_passwords.py
python3 session03/task3_notesapp/test_https.py
```

For the root application, use `docker compose up -d --build` and `docker compose exec -T web python test_passwords.py`. The password test creates temporary test users and removes them afterward; it also checks migration rollback and repeatability. Other deliberately insecure course features remain.
