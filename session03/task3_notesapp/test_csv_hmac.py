"""Run with python3 -m unittest discover -s session03/task3_notesapp -p test_csv_hmac.py."""
import hashlib
import hmac
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).parent / 'web'))
from csv_hmac import load_hmac_key, sign_csv, signed_archive, verify_csv


class CsvHmacTest(unittest.TestCase):
    key = bytes(range(32))
    payload = 'student,class,grade,comment\r\nalice,CS,18,"café 中文, good"\r\n'.encode()

    def test_signature_and_tampering(self):
        signature = sign_csv(self.payload, self.key)
        self.assertEqual(signature, hmac.new(self.key, self.payload, hashlib.sha256).hexdigest())
        self.assertTrue(verify_csv(self.payload, signature, self.key))
        for changed in (self.payload.replace(b'18', b'19'), self.payload[:-1],
                        self.payload + b'\n', self.payload.replace(b'\r\n', b'\n')):
            self.assertFalse(verify_csv(changed, signature, self.key))
        self.assertFalse(verify_csv(self.payload, signature, b'x' * 32))
        for malformed in ('', 'z' * 64, '中' * 64, signature + '\n'):
            self.assertFalse(verify_csv(self.payload, malformed, self.key))

    def test_archive_and_cli(self):
        data = signed_archive(self.payload, self.key)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(sorted(archive.namelist()), ['grades.csv', 'grades.csv.hmac'])
            self.assertEqual(archive.read('grades.csv'), self.payload)
        with tempfile.TemporaryDirectory() as directory:
            key_path = Path(directory) / 'key'
            key_path.write_bytes(self.key)
            archive_path = Path(directory) / 'grades.zip'
            archive_path.write_bytes(data)
            command = [sys.executable, str(Path(__file__).parent / 'web/csv_hmac.py'),
                       str(archive_path), '--key', str(key_path)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            key_path.write_bytes(b'x' * 32)
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
            key_path.write_bytes(b'short')
            with self.assertRaises(ValueError):
                load_hmac_key(key_path)


if __name__ == '__main__':
    unittest.main()
