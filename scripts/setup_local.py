"""Prepare local coursework secrets without printing or replacing their values."""
import argparse
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys


def prepare(root):
    if shutil.which('openssl') is None:
        raise SystemExit('OpenSSL is required on the host; install it before setup.')
    directory = root / '.secrets'
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink():
        raise SystemExit('Refusing a symlink for the secrets directory.')
    os.chmod(directory, 0o700)
    raw_keys = {'comment.key', 'csv_hmac.key', 'session.key', 'jwt.key'}
    for name in sorted(raw_keys | {'db_password', 'db_admin_password'}):
        path = directory / name
        if path.is_symlink():
            raise SystemExit(f'Refusing a symlink for {name}.')
        if path.exists():
            value = path.read_bytes()
            valid = len(value) == 32 if name in raw_keys else len(value.strip()) >= 32
            if not valid:
                raise SystemExit(f'{name} is malformed; restore it rather than overwriting it.')
        else:
            value = secrets.token_bytes(32) if name in raw_keys else secrets.token_hex(32).encode()
            # Compose local secrets preserve host file modes. Read-only files in
            # an owner-only directory also work for non-root Linux containers.
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(value)
        os.chmod(path, 0o444)
    subprocess.run([sys.executable, str(root / 'nginx/create_tls_cert.py')], check=True)
    print('Local secrets ready (existing values preserved); keep .secrets with your database backup.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    prepare(args.root.resolve())


if __name__ == '__main__':
    main()
