"""Argon2id password storage; root login upgrades legacy values after success."""
from argon2 import PasswordHasher, Type, extract_parameters
from argon2.exceptions import InvalidHashError, VerificationError

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=Type.ID)


def hash_password(password):
    if not isinstance(password, str) or not 1 <= len(password) <= 1024:
        raise ValueError("Invalid password length")
    return hasher.hash(password)


def verify_password(encoded, password):
    """Verify an encoded hash only; legacy handling belongs to the login route."""
    if not isinstance(encoded, str) or not isinstance(password, str):
        return False
    if not 1 <= len(password) <= 1024 or not encoded.startswith("$argon2") or not encoded.isascii():
        return False
    try:
        parameters = extract_parameters(encoded)
        # Refuse corrupted/unexpected hashes requesting excessive CPU or memory.
        if (parameters.type != Type.ID or parameters.memory_cost > 262144
                or parameters.time_cost > 10 or parameters.parallelism > 8):
            return False
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError, ValueError):
        return False
