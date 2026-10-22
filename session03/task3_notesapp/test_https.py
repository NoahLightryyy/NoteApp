"""End-to-end local HTTPS login/export check. Run after docker compose up."""
import http.cookiejar
import io
from pathlib import Path
import ssl
import sys
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'web'))
from csv_hmac import load_hmac_key, verify_csv

context = ssl.create_default_context(cafile=str(ROOT / 'secrets/tls/localhost.crt'))
cookies = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context),
                                    urllib.request.HTTPCookieProcessor(cookies))
with client.open('http://localhost:8081/healthz', timeout=15) as response:
    assert response.url == 'https://localhost:8443/healthz'
    assert response.read() == b'ok'
credentials = urllib.parse.urlencode({'username': 'prof.turing', 'password': 'teach123'}).encode()
with client.open('https://localhost:8443/login', credentials, timeout=15) as response:
    assert response.url == 'https://localhost:8443/teacher'
session_cookie = next(cookie for cookie in cookies if cookie.name == 'session')
assert session_cookie.secure
assert session_cookie.has_nonstandard_attr('HttpOnly')
assert session_cookie.get_nonstandard_attr('SameSite') == 'Lax'
with client.open('https://localhost:8443/export.csv?class_id=1&signed=1', timeout=15) as response:
    assert response.headers.get_content_type() == 'application/zip'
    with zipfile.ZipFile(io.BytesIO(response.read())) as archive:
        payload = archive.read('grades.csv')
        signature = archive.read('grades.csv.hmac').decode().strip()
    assert verify_csv(payload, signature, load_hmac_key(ROOT / 'secrets/csv_hmac.key'))
    assert not verify_csv(payload + b'tampered', signature, load_hmac_key(ROOT / 'secrets/csv_hmac.key'))
print('PASS: verified TLS certificate, HTTP redirect, login, secure cookie, CSV HMAC and tamper rejection.')
