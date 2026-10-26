"""Connections use a dedicated least-privilege application account."""
import os
from pathlib import Path
import psycopg2
import psycopg2.extras


def get_db():
    password = Path(os.environ.get('DB_PASSWORD_FILE', '/run/secrets/db_password')).read_text().strip()
    if len(password) < 32:
        raise ValueError('A generated database password file is required.')
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'), dbname=os.environ.get('DB_NAME', 'notesapp'),
        user=os.environ.get('DB_USER', 'notesapp_app'), password=password,
        connect_timeout=5, options='-c statement_timeout=5000 -c lock_timeout=5000',
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    conn.autocommit = True
    return conn
