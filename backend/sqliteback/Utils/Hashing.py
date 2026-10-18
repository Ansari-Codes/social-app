"""
Utils/hashing.py — Password hashing helpers.

Uses PBKDF2-HMAC-SHA256 from the stdlib. Replace with bcrypt/argon2 in prod.
"""

import base64
import hashlib
import hmac
import os

_ITERATIONS = 600_000
_MIN_VERIFY_ITERATIONS = 100_000
_MAX_VERIFY_ITERATIONS = 2_000_000
_SALT_BYTES = 16
_DKLEN = 32


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS, dklen=_DKLEN
    )
    return "pbkdf2_sha256${}${}${}".format(
        _ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(dk).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iters_s, salt_b64, dk_b64 = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iters = int(iters_s)
        if not _MIN_VERIFY_ITERATIONS <= iters <= _MAX_VERIFY_ITERATIONS:
            return False
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(dk_b64, validate=True)
        if not _SALT_BYTES <= len(salt) <= 64 or len(expected) != _DKLEN:
            return False
    except Exception:
        return False

    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iters, dklen=len(expected)
    )
    return hmac.compare_digest(dk, expected)