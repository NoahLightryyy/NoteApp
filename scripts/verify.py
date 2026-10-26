"""Run the current application in a disposable Compose project and database."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import http.cookiejar
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORIES = ('web', 'tests', 'db', 'nginx', 'scripts')
SOURCE_FILES = ('.dockerignore', 'docker-compose.yml', 'docker-compose.http-lab.yml',
                'docker-compose.https.yml')
PASSED_CHECKS = []


def run(command, *, cwd=ROOT, env=None, capture=False):
    result = subprocess.run(command, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.STDOUT if capture else None)
    if result.returncode:
        if capture:
            print(result.stdout, flush=True)
        raise RuntimeError(f'Command failed ({result.returncode}): {command[:4]}')
    return result.stdout if capture else ''


def source_manifest():
    paths = []
    for directory in SOURCE_DIRECTORIES:
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and not any(p in {'__pycache__', 'certs', '.DS_Store'} for p in path.parts):
                if path.suffix != '.pyc':
                    paths.append(path)
    paths.extend(ROOT / name for name in SOURCE_FILES)
    records = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    digest = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    return records, digest


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def check(condition, description):
    if not condition:
        raise AssertionError(description)
    PASSED_CHECKS.append(description)
    print('PASS: ' + description, flush=True)


def verify_http(root, https_port, http_port):
    context = ssl.create_default_context(cafile=str(root / 'nginx/certs/notesapp.crt'))
    base = f'https://localhost:{https_port}'
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context),
                                        urllib.request.HTTPCookieProcessor(cookies))
    with opener.open(base + '/healthz', timeout=10) as response:
        check(response.read() == b'ok', 'certificate-validated HTTPS health check')
    with opener.open(f'http://localhost:{http_port}/healthz', timeout=10) as response:
        check(response.url == base + '/healthz', 'HTTP redirects to the correct HTTPS port')
    with opener.open(base + '/login', timeout=10) as response:
        form = response.read().decode()
    token = re.search(r'name="csrf_token"\s+value="([^"]+)"', form).group(1)
    payload = urllib.parse.urlencode({'username': 'prof.turing', 'password': 'teach123',
                                      'csrf_token': token}).encode()
    with opener.open(base + '/login', data=payload, timeout=15) as response:
        check(response.url.endswith('/teacher'), 'teacher login through HTTPS with CSRF')
    check(bool(list(cookies)) and all(c.secure for c in cookies), 'HTTPS session cookies have Secure enabled')
    with opener.open(base + '/export.csv?signed=1', timeout=10) as response:
        archive = response.read()
    sys.path.insert(0, str(root / 'web'))
    from csv_hmac import verify_csv
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        csv_bytes = bundle.read('grades.csv')
        signature = bundle.read('grades.csv.hmac').decode().strip()
    key = (root / '.secrets/csv_hmac.key').read_bytes()
    check(verify_csv(csv_bytes, signature, key), 'real HTTPS ZIP export authenticates')
    check(not verify_csv(csv_bytes + b'x', signature, key), 'altered downloaded CSV fails authentication')


def verify_http_lab(port):
    """Exercise the intentionally insecure capture mode, only in this test stack."""
    base = f'http://127.0.0.1:{port}'
    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    with opener.open(base + '/login', timeout=10) as response:
        form = response.read().decode()
    token = re.search(r'name="csrf_token"\s+value="([^"]+)"', form).group(1)
    payload = urllib.parse.urlencode({'username': 'alice', 'password': 'alicepw',
                                      'csrf_token': token}).encode()
    with opener.open(base + '/login', data=payload, timeout=15) as response:
        check(response.url == base + '/dashboard', 'opt-in HTTP capture mode supports a real login')
    check(bool(list(cookies)) and all(not c.secure for c in cookies),
          'HTTP capture mode explicitly uses non-Secure session cookies')


def verify_bounded_burst(root, https_port):
    """120 local requests, at most 12 concurrent; never targets another project."""
    context = ssl.create_default_context(cafile=str(root / 'nginx/certs/notesapp.crt'))
    url = f'https://localhost:{https_port}/healthz'
    def request_once(_):
        try:
            with urllib.request.urlopen(url, context=context, timeout=10) as response:
                response.read()
                return response.status
        except urllib.error.HTTPError as error:
            error.close()
            return error.code
    with ThreadPoolExecutor(max_workers=12) as pool:
        counts = Counter(pool.map(request_once, range(120)))
    check(counts[200] > 0 and counts[429] > 0 and set(counts) <= {200, 429},
          'bounded 120-request local burst is rate limited without server errors')
    time.sleep(2)
    check(request_once(None) == 200, 'HTTPS health recovers after the bounded burst')
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT / '.verification/latest.json')
    args = parser.parse_args()
    if not shutil.which('docker'):
        raise SystemExit('Docker with Compose is required.')
    records, digest = source_manifest()
    report = {'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'git_head': run(['git', 'rev-parse', 'HEAD'], capture=True).strip(),
              'source_sha256': digest, 'source_files': records,
              'scope': 'fresh disposable database, generated keys, current source; no existing data used',
              'passed': False, 'cleanup_succeeded': False, 'passed_checks': PASSED_CHECKS}
    project = 'notesapp-verify-' + uuid.uuid4().hex[:10]
    report['compose_project'] = project
    https_port, http_port = free_port(), free_port()
    while http_port == https_port:
        http_port = free_port()
    lab_port = free_port()
    while lab_port in (https_port, http_port):
        lab_port = free_port()
    env = dict(os.environ, NOTESAPP_DB_NAME='notesapp_test',
               NOTESAPP_HTTPS_PORT=str(https_port), NOTESAPP_HTTP_PORT=str(http_port),
               NOTESAPP_HTTP_LAB_PORT=str(lab_port))
    # Never inherit a user-selected project or extra Compose file.
    env.pop('COMPOSE_FILE', None)
    env.pop('COMPOSE_PROJECT_NAME', None)
    failure = None
    with tempfile.TemporaryDirectory(prefix='notesapp-verification-') as temporary:
        root = Path(temporary)
        for directory in SOURCE_DIRECTORIES:
            shutil.copytree(ROOT / directory, root / directory,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'certs', '.DS_Store'))
        for name in SOURCE_FILES:
            shutil.copy2(ROOT / name, root / name)
        compose = ['docker', 'compose', '-p', project, '-f', str(root / 'docker-compose.yml')]
        def dc(*arguments, capture=False):
            return run(compose + list(arguments), cwd=root, env=env, capture=capture)
        try:
            run([sys.executable, str(root / 'scripts/setup_local.py')], cwd=root, env=env)
            config = json.loads(dc('config', '--format', 'json', capture=True))
            check(not config['services']['db'].get('ports'), 'database has no host port')
            check(not config['services']['web'].get('ports'), 'Flask has no direct host port')
            check(config['services']['web'].get('read_only') is True, 'application filesystem is read-only')
            dc('up', '-d', '--build', '--wait', '--wait-timeout', '180')
            output = dc('exec', '-T', '-e', 'NOTESAPP_TEST_DATABASE=1', 'web',
                        'python', '-m', 'unittest', 'discover', '-s', 'tests', '-v', capture=True)
            print(output, flush=True)
            report['test_output'] = output
            match = re.search(r'Ran (\d+) tests?', output)
            if not match or int(match.group(1)) == 0 or '\nOK' not in output:
                raise AssertionError('The test suite did not report a nonzero successful run.')
            report['tests_run'] = int(match.group(1))
            role = dc('exec', '-T', 'web', 'python', '-c',
                      'from database import get_db; c=get_db(); q=c.cursor(); q.execute("SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user"); print(list(q.fetchone().values())); c.close()', capture=True)
            check('[False, False, False]' in role, 'application database role is not privileged')
            uid = dc('exec', '-T', 'web', 'id', '-u', capture=True).strip()
            check(uid != '0', 'application process is not root')
            report['resolved_dependencies'] = dc('exec', '-T', 'web', 'python', '-m', 'pip', 'freeze', capture=True).splitlines()
            verify_http(root, https_port, http_port)
            # Re-start migration against ciphertext to verify idempotent startup.
            dc('exec', '-T', 'web', 'python', 'migrate_comments.py')
            run(compose + ['-f', str(root / 'docker-compose.http-lab.yml'),
                           'up', '-d', '--wait', '--wait-timeout', '180'], cwd=root, env=env)
            verify_http_lab(lab_port)
            dc('up', '-d', '--wait', '--wait-timeout', '180')
            verify_http(root, https_port, http_port)
            with socket.socket() as probe:
                probe.settimeout(3)
                check(probe.connect_ex(('127.0.0.1', lab_port)) != 0,
                      'restoring default Compose removes the direct plaintext app port')
            report['bounded_burst_status_counts'] = verify_bounded_burst(root, https_port)
            report['passed'] = True
        except Exception as error:
            failure = error
            report['error'] = str(error)
            try:
                print(dc('logs', '--no-color', '--tail', '40', 'web', 'db', 'nginx', capture=True))
            except Exception:
                pass
        finally:
            try:
                dc('down', '--volumes', '--remove-orphans')
                report['cleanup_succeeded'] = True
            except Exception as error:
                failure = failure or error
                report['passed'] = False
                report['cleanup_error'] = str(error)
    report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Verification record: {args.report.resolve()}')
    if failure:
        raise SystemExit(f'FAIL: {failure}')
    print('PASS: isolated verification completed; temporary containers and database volume removed.')


if __name__ == '__main__':
    main()
