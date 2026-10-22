"""Integration checks; run inside the web container against the course database."""
from contextlib import closing
from uuid import uuid4
from argon2 import PasswordHasher, Type
from app import app, get_db
from password_security import hash_password, verify_password, hasher


def query(sql, params=(), fetch=False):
    with closing(get_db()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() if fetch else None


def snapshot():
    return query('SELECT id, password FROM users ORDER BY id', fetch=True)


def stored(name):
    return query('SELECT password FROM users WHERE username=%s', (name,), True)[0]['password']


prefix = 'argon_test_' + uuid4().hex
names = [prefix + suffix for suffix in ('legacy', 'broken', 'created', 'old')]
secret = "test-'密碼-123"
try:
    first, second = hash_password(secret), hash_password(secret)
    assert first != second and verify_password(first, secret)
    assert not verify_password(first, 'wrong')
    assert not verify_password('plaintext', 'plaintext')
    assert not verify_password('$argon2id$broken', secret)
    for name, password in zip(names[:2], [secret, '$argon2id$broken']):
        query('INSERT INTO users(username,password,role) VALUES(%s,%s,%s)', (name,password,'student'))
    client = app.test_client()
    assert client.post('/login', data={'username': names[0], 'password': 'wrong'}).status_code == 200
    assert stored(names[0]) == secret
    assert client.post('/login', data={'username': names[0], 'password': secret}).status_code == 302
    assert verify_password(stored(names[0]), secret)
    client.get('/logout')
    for username, password in [(names[0], 'wrong'), ('missing_'+prefix, secret), ("' OR 1=1 --", secret)]:
        response = client.post('/login', data={'username':username,'password':password})
        assert response.status_code == 200 and b'Invalid credentials' in response.data
        with client.session_transaction() as session:
            assert 'user_id' not in session
    for username,password in [('alice','alicepw'),('prof.turing','teach123'),('admin','admin123')]:
        assert client.post('/login', data={'username':username,'password':password}).status_code == 302
        client.get('/logout')
    # Exercise the actual admin form and stored result.
    admin = app.test_client()
    with admin.session_transaction() as session:
        session.update(user_id=1,username='admin',role='admin')
    assert admin.post('/admin/users', data={'action':'create','username':names[2],'password':secret,'role':'student'}).status_code == 302
    assert stored(names[2]).startswith('$argon2id$') and verify_password(stored(names[2]),secret)
    assert client.post('/login',data={'username':names[2],'password':secret}).status_code == 302
    old = PasswordHasher(time_cost=1,memory_cost=8192,parallelism=1,type=Type.ID).hash(secret)
    query('INSERT INTO users(username,password,role) VALUES(%s,%s,%s)', (names[3],old,'student'))
    assert client.post('/login',data={'username':names[3],'password':secret}).status_code == 302
    refreshed=stored(names[3])
    assert refreshed != old and not hasher.check_needs_rehash(refreshed)
    assert verify_password(refreshed,secret)
finally:
    query('DELETE FROM users WHERE username = ANY(%s)', (names,))
print('PASS: Argon2id salts, correct/wrong passwords, legacy login upgrade, SQL injection rejection, demo logins, admin creation and rehash.')
