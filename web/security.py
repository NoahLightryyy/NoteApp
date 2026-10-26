"""Small, testable security primitives for the local coursework deployment."""
from collections import OrderedDict, deque
from decimal import Decimal, InvalidOperation
import ipaddress
import os
from pathlib import Path
import re
import threading
import time

import jwt

ROLES = frozenset({"student", "teacher", "admin"})
JWT_ISSUER = "notesapp"
JWT_AUDIENCE = "notesapp-api"
JWT_LIFETIME_SECONDS = 900
MAX_PASSWORD_LENGTH = 1024
MAX_COMMENT_LENGTH = 4000


def load_secret(variable, default_path):
    """Fail startup if a required raw 256-bit secret is absent or malformed."""
    key = Path(os.environ.get(variable, default_path)).read_bytes()
    if len(key) != 32:
        raise ValueError(f"{variable} must refer to exactly 32 raw bytes")
    return key


def issue_token(user_id, key, auth_version, now=None):
    now = int(time.time() if now is None else now)
    return jwt.encode({"sub": str(positive_id(user_id)), "iat": now,
                       "exp": now + JWT_LIFETIME_SECONDS,
                       "iss": JWT_ISSUER, "aud": JWT_AUDIENCE,
                       "ver": auth_version_value(auth_version)},
                      key, algorithm="HS256")


def decode_token(token, key):
    if not isinstance(token, str) or len(token) > 4096:
        return None
    try:
        claims = jwt.decode(token, key, algorithms=["HS256"],
                            issuer=JWT_ISSUER, audience=JWT_AUDIENCE,
                            options={"require": ["sub", "iat", "exp", "iss", "aud", "ver"]})
        if type(claims["iat"]) is not int or type(claims["exp"]) is not int:
            return None
        if not 0 < claims["exp"] - claims["iat"] <= JWT_LIFETIME_SECONDS:
            return None
        claims["user_id"] = positive_id(claims["sub"])
        claims["ver"] = auth_version_value(claims["ver"])
        return claims
    except (jwt.InvalidTokenError, ValueError, TypeError):
        return None


def auth_version_value(value):
    if type(value) is not int or value < 0:
        raise ValueError("Invalid authentication version")
    return value


def positive_id(value):
    if isinstance(value, bool) or not re.fullmatch(r"[1-9][0-9]{0,9}", str(value)):
        raise ValueError("Invalid identifier")
    result = int(value)
    if result > 2147483647:
        raise ValueError("Invalid identifier")
    return result


def bounded_text(value, maximum, *, required=False):
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value:
        raise ValueError("Invalid text")
    if required and not value:
        raise ValueError("Required text")
    return value


def username_value(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.@-]{1,80}", value):
        raise ValueError("Invalid username")
    return value


def role_value(value):
    if value not in ROLES:
        raise ValueError("Invalid role")
    return value


def grade_value(value):
    try:
        bounded_text(value, 16, required=True)
        grade = Decimal(value)
        if not grade.is_finite() or not 0 <= grade <= 20 or grade != grade.quantize(Decimal("0.1")):
            raise ValueError("Grade must be 0–20 with at most one decimal place")
        return grade
    except InvalidOperation as error:
        raise ValueError("Invalid grade") from error


def csv_cell(value):
    """Keep spreadsheet programs from interpreting untrusted text as formulas."""
    if value is None:
        return ""
    if isinstance(value, str):
        # Leading whitespace/control characters can hide a formula prefix.
        probe = value.lstrip(" \t\r\n\v\f\ufeff")
        if (probe and probe[0] in "=+-@") or value.startswith(("\t", "\r", "\n")):
            return "'" + value
    return value


def loopback_host(value):
    value = bounded_text(value, 45, required=True).strip()
    if value.lower() == "localhost":
        return "127.0.0.1"
    try:
        address = ipaddress.ip_address(value)
    except ValueError as error:
        raise ValueError("Only a loopback address is allowed") from error
    if not address.is_loopback:
        raise ValueError("Only a loopback address is allowed")
    return str(address)


class LoginLimiter:
    """Bounded per-process attempt windows; restart resets this local-lab limiter.

    An IP budget bounds expensive Argon2 operations; a username budget also
    limits distributed guesses. The reverse proxy address is intentionally used
    unless a trusted proxy layer is explicitly configured by the deployment.
    """
    def __init__(self, window=300, per_ip=30, per_username=10, capacity=10000):
        self.window = window
        self.per_ip = per_ip
        self.per_username = per_username
        self.capacity = capacity
        self._buckets = OrderedDict()
        self._lock = threading.Lock()

    def allow(self, address, username, now=None):
        now = time.monotonic() if now is None else now
        keys = (("ip", address), ("username", username))
        with self._lock:
            # Expire old entries before enforcing the memory cap. If full, fail
            # closed rather than evicting active counters that an attacker can reset.
            for key, bucket in list(self._buckets.items()):
                while bucket and bucket[0] <= now - self.window:
                    bucket.popleft()
                if not bucket:
                    del self._buckets[key]
            new_count = sum(key not in self._buckets for key in keys)
            if len(self._buckets) + new_count > self.capacity:
                return False
            for key, limit in zip(keys, (self.per_ip, self.per_username)):
                if len(self._buckets.get(key, ())) >= limit:
                    return False
            for key in keys:
                self._buckets.setdefault(key, deque()).append(now)
            return True

    def reset(self):
        """Clear process-local counters; useful for isolated test fixtures."""
        with self._lock:
            self._buckets.clear()
