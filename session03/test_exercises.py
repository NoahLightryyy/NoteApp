"""Run with: python test_exercises.py (no database needed)."""
import base64
from contextlib import redirect_stdout
import io
import sys
import tempfile
import unittest
from pathlib import Path
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from task1_caesar import caesar, crack
from task2_images import compare
from PIL import Image
# C3 is maintained in the root application; exercise its pure crypto module.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'web'))
from comment_crypto import encrypt_comment, decrypt_comment, PREFIX


class ExercisesTest(unittest.TestCase):
    def test_caesar_roundtrip_all_keys(self):
        text = 'Hello, Zebra! 123 中文 é'
        for key in range(26):
            self.assertEqual(caesar(caesar(text, key), -key), text)

    def test_frequency_attack_without_key(self):
        text = ('The students are learning about computer security and encryption. '
                'They read the messages and examine the letters to discover the secret. '
                'This exercise explains how the frequency of common English letters '
                'can help reveal a hidden message without knowing the encryption key.')
        self.assertEqual(crack(caesar(text, 13))[0][1:], (13, text))
        with self.assertRaises(ValueError):
            crack('123!')

    def test_comment_roundtrip(self):
        key = AESGCM.generate_key(bit_length=256)
        for text in [None, '', 'Well done!', '中文 café 🦊', PREFIX + 'literal plaintext']:
            self.assertEqual(decrypt_comment(encrypt_comment(text, 4, key), 4, key), text)
        self.assertNotEqual(encrypt_comment('same', 4, key), encrypt_comment('same', 4, key))

    def test_comment_authentication(self):
        key = AESGCM.generate_key(bit_length=256)
        envelope = encrypt_comment('private', 4, key)
        with self.assertRaises(InvalidTag):
            decrypt_comment(envelope, 5, key)  # Row swapping is rejected.
        with self.assertRaises(InvalidTag):
            decrypt_comment(envelope, 4, AESGCM.generate_key(bit_length=256))
        raw = bytearray(base64.b64decode(envelope[len(PREFIX):]))
        raw[-1] ^= 1
        with self.assertRaises(InvalidTag):
            decrypt_comment(PREFIX + base64.b64encode(raw).decode(), 4, key)
        with self.assertRaises(ValueError):
            decrypt_comment('plaintext', 4, key)

    def test_synthetic_image_roundtrip(self):
        original = Image.new('RGB', (32, 32), 'white')
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            result = compare(original, Path(directory))
            self.assertTrue(result['gcm_tamper_rejected'])
            with Image.open(Path(directory) / 'gcm_decrypted.png') as restored:
                self.assertEqual(restored.tobytes(), original.tobytes())
            with Image.open(Path(directory) / 'ecb_encrypted.png') as encrypted:
                data = encrypted.tobytes()
                self.assertEqual(data[:16], data[16:32])


if __name__ == '__main__':
    unittest.main()
