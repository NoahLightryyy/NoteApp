"""AES-256-GCM envelopes for notes.comment. Never store the key in PostgreSQL."""
import base64
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PREFIX = 'gcm1:'


def load_key():
    path = Path(os.environ.get('COMMENT_KEY_FILE', '/run/secrets/comment_key'))
    key = path.read_bytes()
    if len(key) != 32:
        raise ValueError('Comment key must contain exactly 32 raw bytes.')
    return key


def associated_data(note_id):
    # Prevent moving a valid encrypted comment to a different note.
    return f'notes.comment:v1:{int(note_id)}'.encode('ascii')


def encrypt_comment(value, note_id, key):
    if value is None:
        return None
    nonce = os.urandom(12)  # A fresh random nonce for EVERY encryption.
    ciphertext_and_tag = AESGCM(key).encrypt(nonce, value.encode('utf-8'), associated_data(note_id))
    return PREFIX + base64.b64encode(nonce + ciphertext_and_tag).decode('ascii')


def decrypt_comment(value, note_id, key):
    if value is None:
        return None
    if not value.startswith(PREFIX):
        raise ValueError('Unencrypted comment: run the migration before starting the app.')
    payload = base64.b64decode(value[len(PREFIX):], validate=True)
    if len(payload) < 28:
        raise ValueError('Truncated encrypted comment.')
    return AESGCM(key).decrypt(payload[:12], payload[12:], associated_data(note_id)).decode('utf-8')
