"""Atomically migrate existing plaintext comments; safe to rerun with same key."""
from contextlib import closing
from comment_crypto import PREFIX, load_key, encrypt_comment, decrypt_comment
from database import get_db


def migrate():
    key = load_key()
    changed = 0
    with closing(get_db()) as conn:
        conn.autocommit = False
        with conn:
            with conn.cursor() as cur:
                cur.execute('LOCK TABLE notes IN ACCESS EXCLUSIVE MODE')
                # A server-side cursor bounds memory even when an existing table
                # is large; updates use a separate cursor in the same transaction.
                with conn.cursor(name='comment_migration') as rows:
                    rows.itersize = 100
                    rows.execute('SELECT id, comment FROM notes ORDER BY id')
                    for row in rows:
                        value = row['comment']
                        if value is None:
                            continue
                        if value.startswith(PREFIX):
                            # Fail rather than silently skipping a damaged envelope/wrong key.
                            decrypt_comment(value, row['id'], key)
                            continue
                        encrypted = encrypt_comment(value, row['id'], key)
                        cur.execute('UPDATE notes SET comment = %s WHERE id = %s', (encrypted, row['id']))
                        changed += 1
    print(f'Migrated {changed} comments. Existing encrypted comments verified.')


if __name__ == '__main__':
    migrate()
