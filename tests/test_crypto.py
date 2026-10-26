"""Cryptographic behavior checks with fresh in-memory keys and fictional data."""
import base64
import io
import os
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))

from cryptography.exceptions import InvalidTag
from comment_crypto import PREFIX, decrypt_comment, encrypt_comment
from csv_hmac import signed_archive, verify_csv
from password_security import hash_password, verify_password
from security import LoginLimiter


class CommentEncryptionTests(unittest.TestCase):
    def test_round_trip_random_nonces_and_record_binding(self):
        key = os.urandom(32)
        plaintext = "Private grade comment — 中文, café\nsecond line"
        first = encrypt_comment(plaintext, 123, key)
        second = encrypt_comment(plaintext, 123, key)
        self.assertTrue(first.startswith(PREFIX))
        self.assertNotIn(plaintext, first)
        self.assertEqual(decrypt_comment(first, 123, key), plaintext)
        self.assertEqual(decrypt_comment(second, 123, key), plaintext)
        self.assertNotEqual(first, second)
        self.assertNotEqual(
            base64.b64decode(first[len(PREFIX):])[:12],
            base64.b64decode(second[len(PREFIX):])[:12],
        )
        with self.assertRaises(InvalidTag):
            decrypt_comment(first, 124, key)
        with self.assertRaises(InvalidTag):
            decrypt_comment(first, 123, os.urandom(32))

    def test_tampering_and_plaintext_fail_closed(self):
        key = os.urandom(32)
        envelope = encrypt_comment("fictional private comment", 8, key)
        payload = bytearray(base64.b64decode(envelope[len(PREFIX):]))
        payload[-1] ^= 1
        changed = PREFIX + base64.b64encode(payload).decode("ascii")
        with self.assertRaises(InvalidTag):
            decrypt_comment(changed, 8, key)
        for invalid in ("unmigrated plaintext", PREFIX + "YQ=="):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                decrypt_comment(invalid, 8, key)
        self.assertIsNone(encrypt_comment(None, 8, key))
        self.assertIsNone(decrypt_comment(None, 8, key))


class CsvAuthenticationTests(unittest.TestCase):
    def test_zip_preserves_exact_bytes_and_authenticates(self):
        key = os.urandom(32)
        csv_bytes = 'student,grade,comment\r\nexample,12.3,"中文, line\nbreak"\r\n'.encode()
        with zipfile.ZipFile(io.BytesIO(signed_archive(csv_bytes, key))) as archive:
            self.assertEqual(sorted(archive.namelist()), ["grades.csv", "grades.csv.hmac"])
            self.assertEqual(archive.read("grades.csv"), csv_bytes)
            signature = archive.read("grades.csv.hmac").decode("ascii").strip()
        self.assertTrue(verify_csv(csv_bytes, signature, key))
        for changed in (
            csv_bytes.replace(b"12.3", b"20.0"), csv_bytes + b"\n",
            csv_bytes.replace(b"\r\n", b"\n"), csv_bytes[:-1],
        ):
            with self.subTest(changed=changed):
                self.assertFalse(verify_csv(changed, signature, key))
        self.assertFalse(verify_csv(csv_bytes, signature, os.urandom(32)))
        for malformed in ("", "z" * 64, signature + "\n", "中" * 64):
            self.assertFalse(verify_csv(csv_bytes, malformed, key))

    def test_independent_random_password_salts(self):
        password = "Fictional fixture password only"
        first, second = hash_password(password), hash_password(password)
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("$argon2id$"))
        self.assertTrue(verify_password(first, password))
        self.assertFalse(verify_password(first, "incorrect"))
        self.assertFalse(verify_password("$argon2id$broken", password))


class LoginLimiterTests(unittest.TestCase):
    def test_address_and_account_budgets_expire(self):
        limiter = LoginLimiter(window=10, per_ip=3, per_username=2)
        self.assertTrue(limiter.allow("ip-a", "user-a", now=0))
        self.assertTrue(limiter.allow("ip-b", "user-a", now=1))
        self.assertFalse(limiter.allow("ip-c", "user-a", now=2))
        self.assertTrue(limiter.allow("ip-a", "user-b", now=2))
        self.assertTrue(limiter.allow("ip-a", "user-c", now=3))
        self.assertFalse(limiter.allow("ip-a", "user-d", now=4))
        self.assertTrue(limiter.allow("ip-a", "user-a", now=14))

    def test_capacity_does_not_evict_active_limits(self):
        limiter = LoginLimiter(window=10, per_ip=1, per_username=1, capacity=2)
        self.assertTrue(limiter.allow("ip-a", "user-a", now=0))
        self.assertFalse(limiter.allow("ip-b", "user-b", now=1))
        self.assertFalse(limiter.allow("ip-a", "user-a", now=2))
        self.assertTrue(limiter.allow("ip-b", "user-b", now=11))
