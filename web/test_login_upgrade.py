"""Test login upgrade using rollback-only database fixtures; no real account changes."""
from uuid import uuid4
from unittest.mock import patch
import app as module
from password_security import verify_password

conn = module.get_db()
conn.autocommit = False
class BorrowedConnection:
    def cursor(self): return conn.cursor()
    def close(self): pass
name = 'lab_upgrade_' + uuid4().hex
secret = 'fixture-password'
try:
    with conn.cursor() as cur:
        cur.execute('INSERT INTO users(username,password,role) VALUES(%s,%s,%s)', (name,secret,'student'))
    def stored():
        with conn.cursor() as cur:
            cur.execute('SELECT password FROM users WHERE username=%s',(name,))
            return cur.fetchone()['password']
    with patch.object(module,'get_db',return_value=BorrowedConnection()), patch.object(module,'log'):
        client=module.app.test_client()
        assert client.post('/login',data={'username':name,'password':'wrong'}).status_code==200
        assert stored()==secret
        assert client.post('/login',data={'username':name,'password':secret}).status_code==302
        encoded=stored()
        assert encoded.startswith('$argon2id$') and verify_password(encoded,secret)
        client.get('/logout')
        assert client.post('/login',data={'username':name,'password':secret}).status_code==302
        assert stored()==encoded
        client.get('/logout')
        for user,pw in [(name,'wrong'),('missing_'+name,secret),("' OR 1=1 --",secret)]:
            assert client.post('/login',data={'username':user,'password':pw}).status_code==200
            with client.session_transaction() as s: assert 'user_id' not in s
        with conn.cursor() as cur:
            cur.execute('UPDATE users SET password=%s WHERE username=%s',('$argon2id$broken',name))
        assert client.post('/login',data={'username':name,'password':secret}).status_code==200
    print('PASS: wrong legacy password leaves storage unchanged; correct login upgrades to Argon2id; second login succeeds without changing hash; wrong/unknown/injection/malformed hash rejected. All fixture changes rolled back.')
finally:
    conn.rollback()
    conn.close()
