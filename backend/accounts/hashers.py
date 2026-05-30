"""
Django password hasher for Flask/werkzeug-format hashes migrated from the legacy stack.

Werkzeug 3.x defaults to scrypt:  scrypt:32768:8:1$<salt>$<hash>  (~162 chars)
Older werkzeug used pbkdf2:        pbkdf2:sha256:<iters>$<salt>$<hash>

Both are stored in the Django password column as:
    werkzeug$<original-werkzeug-hash>

The "werkzeug" algorithm prefix makes Django's identify_hasher() select this class
for any migrated password, regardless of the inner hash algorithm.

On first successful login, must_update() returns True, which triggers Django to
re-hash the password using the native PBKDF2 hasher — silently upgrading the user.
"""
from django.contrib.auth.hashers import BasePasswordHasher

ALGORITHM = "werkzeug"


class WerkzeugPasswordHasher(BasePasswordHasher):
    algorithm = ALGORITHM

    def verify(self, password: str, encoded: str) -> bool:
        _, werkzeug_hash = encoded.split("$", 1)
        from werkzeug.security import check_password_hash
        return check_password_hash(werkzeug_hash, password)

    def encode(self, password: str, salt: str) -> str:
        raise NotImplementedError("Use the native PBKDF2 hasher for new passwords")

    def safe_summary(self, encoded: str) -> dict:
        return {"algorithm": self.algorithm, "hash": encoded[-8:]}

    def must_update(self, encoded: str) -> bool:
        return True


def wrap_werkzeug_hash(password_hash: str | None) -> str:
    """
    Wrap a raw werkzeug hash so Django's identify_hasher() routes to WerkzeugPasswordHasher.

    Handles both werkzeug hash formats:
      - scrypt:N:r:p$<salt>$<hash>             (werkzeug >= 2.3 default, ~162 chars)
      - pbkdf2:sha256:<iters>$<salt>$<hash>    (werkzeug < 2.3 default)

    Returns "!" (unusable password) if password_hash is None or empty.
    """
    if not password_hash:
        return "!"
    if password_hash.startswith(("pbkdf2:", "scrypt:")):
        return f"{ALGORITHM}${password_hash}"
    return password_hash
