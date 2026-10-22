"""Authenticate the exact exported CSV bytes with a dedicated HMAC-SHA256 key."""
import argparse
import hashlib
import hmac
import io
import os
from pathlib import Path
import re
import zipfile


def load_hmac_key(path=None):
    key = Path(path or os.environ.get('CSV_HMAC_KEY_FILE',
                                     '/run/secrets/csv_hmac_key')).read_bytes()
    if len(key) != 32:
        raise ValueError('CSV HMAC key must contain exactly 32 raw bytes.')
    return key


def sign_csv(payload, key):
    if len(key) != 32:
        raise ValueError('CSV HMAC key must contain exactly 32 raw bytes.')
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def verify_csv(payload, signature, key):
    if not isinstance(signature, str) or not re.fullmatch(r'[0-9a-f]{64}', signature):
        return False
    return hmac.compare_digest(sign_csv(payload, key), signature)


def signed_archive(payload, key):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('grades.csv', payload)
        archive.writestr('grades.csv.hmac', sign_csv(payload, key) + '\n')
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description='Verify a signed CSV export ZIP.')
    parser.add_argument('archive', type=Path)
    parser.add_argument('--key', required=True, type=Path)
    args = parser.parse_args()
    try:
        key = load_hmac_key(args.key)
        with zipfile.ZipFile(args.archive) as archive:
            if sorted(archive.namelist()) != ['grades.csv', 'grades.csv.hmac']:
                raise ValueError('Unexpected archive contents.')
            payload = archive.read('grades.csv')
            signature = archive.read('grades.csv.hmac').decode('ascii').removesuffix('\n')
        if not verify_csv(payload, signature, key):
            raise ValueError('CSV authentication failed.')
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f'FAIL: {error}\n')
    print('OK: CSV HMAC-SHA256 verified.')


if __name__ == '__main__':
    main()
