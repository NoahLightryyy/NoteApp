"""Create a persistent local lab key; refuse to overwrite an existing key."""
import os
import secrets
from pathlib import Path

if __name__ == '__main__':
    directory = Path(__file__).resolve().parent / 'secrets'
    directory.mkdir(mode=0o700, exist_ok=True)
    for name in ('comment.key', 'csv_hmac.key'):
        path = directory / name
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            print(f'{name} already exists; kept unchanged.')
        else:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(secrets.token_bytes(32))
            print(f'Created secrets/{name}. Keep it private and backed up.')
