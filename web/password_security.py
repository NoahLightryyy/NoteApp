"""Argon2id password storage and transactional legacy-data migration."""
from contextlib import closing
from argon2 import PasswordHasher, Type, extract_parameters
from argon2.exceptions import InvalidHashError, VerificationError

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=Type.ID)


def hash_password(password):
    return hasher.hash(password)


def verify_password(encoded, password):
    # Never accept legacy plaintext through the login endpoint.
    if not encoded.startswith("$argon2") or not encoded.isascii():
        return False
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def migrate_passwords(get_db):
    """Hash existing plaintext once; retain valid Argon2 hashes on reruns."""
    changed = 0
    with closing(get_db()) as conn:
        conn.autocommit = False
        with conn:
            with conn.cursor() as cur:
                cur.execute('LOCK TABLE users IN ACCESS EXCLUSIVE MODE')
                cur.execute('SELECT id, password FROM users ORDER BY id')
                for row in cur.fetchall():
                    value = row['password']
                    if value.startswith('$argon2'):
                        extract_parameters(value)  # Fail closed on malformed stored hashes.
                        continue
                    cur.execute('UPDATE users SET password = %s WHERE id = %s',
                                (hash_password(value), row['id']))
                    changed += 1
    return changed
