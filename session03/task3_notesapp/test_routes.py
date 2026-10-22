"""Integration test for the separate lab database. Run inside its web container."""
import io
import zipfile
from csv_hmac import load_hmac_key, verify_csv
from contextlib import closing
from app import app, get_db
from migrate_comments import migrate
from comment_crypto import decrypt_comment, PREFIX, load_key


def query(sql, parameters=(), one=False):
    with closing(get_db()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, parameters)
            if cur.description:
                return cur.fetchone() if one else cur.fetchall()


before = query('SELECT id, comment FROM notes ORDER BY id')
assert before and all(r['comment'] is None or r['comment'].startswith(PREFIX) for r in before)
migrate()
assert query('SELECT id, comment FROM notes ORDER BY id') == before
client = app.test_client()
with client.session_transaction() as session:
    session.update(user_id=6, username='alice', role='student')
assert b'Late submission, but good quality.' in client.get('/dashboard').data
assert client.get('/api/notes/1').json['comment'] == 'Late submission, but good quality.'
with client.session_transaction() as session:
    session.update(user_id=2, username='prof.turing', role='teacher')
assert client.get('/teacher').status_code == 200
csv_response = client.get('/export.csv?class_id=1')
assert b'Late submission, but good quality.' in csv_response.data
assert verify_csv(csv_response.data, csv_response.headers['X-CSV-HMAC-SHA256'], load_hmac_key())
for query_string in ('?class_id=1&signed=1', '?signed=1'):
    response = client.get('/export.csv' + query_string)
    assert response.status_code == 200 and response.mimetype == 'application/zip'
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        payload = archive.read('grades.csv')
        signature = archive.read('grades.csv.hmac').decode('ascii').strip()
    assert verify_csv(payload, signature, load_hmac_key())
    assert signature == response.headers['X-CSV-HMAC-SHA256']
    assert not verify_csv(payload + b'changed', signature, load_hmac_key())
original = query('SELECT grade, comment FROM notes WHERE id=1', one=True)
new_id = None
try:
    response = client.post('/grades', data={'note_id':'1', 'grade':'17.1', 'comment':'Updated café 中文'})
    assert response.status_code == 302
    row = query('SELECT comment FROM notes WHERE id=1', one=True)
    assert row['comment'].startswith(PREFIX) and 'Updated' not in row['comment']
    assert client.get('/api/notes/1').json['comment'] == 'Updated café 中文'
    assert 'Updated café 中文' in client.get('/teacher').get_data(as_text=True)
    assert 'Updated café 中文' in client.get('/export.csv').get_data(as_text=True)
    query('UPDATE notes SET comment=%s WHERE id=1', (PREFIX + 'A' * 40,))
    assert client.get('/api/notes/1').status_code == 500
    assert b'authentication failed' in client.get('/api/notes/1').data
    existing = {r['id'] for r in query('SELECT id FROM notes')}
    assert client.post('/grades', data={'student_id':'6', 'class_id':'1', 'grade':'12', 'comment':'New test comment'}).status_code == 302
    added = [r for r in query('SELECT id, comment FROM notes') if r['id'] not in existing]
    assert len(added) == 1
    new_id = added[0]['id']
    assert decrypt_comment(added[0]['comment'], new_id, load_key()) == 'New test comment'
finally:
    query('UPDATE notes SET grade=%s, comment=%s WHERE id=1', (original['grade'], original['comment']))
    if new_id is not None:
        query('DELETE FROM notes WHERE id=%s', (new_id,))
assert query('SELECT id, comment FROM notes ORDER BY id') == before
print('PASS: migration rerun, dashboard, API, teacher, CSV, update, insert, tamper rejection; test rows restored.')
