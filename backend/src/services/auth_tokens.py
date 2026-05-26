from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from config.settings import get_settings
from utils.exceptions import InvalidTokenError

SETTINGS = get_settings()


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def issue_access_token(user_id: str) -> str:
    exp = datetime.now(tz=UTC) + timedelta(hours=1)
    return jwt.encode({"sub": user_id, "exp": exp}, SETTINGS.jwt_secret, algorithm="HS256")


def issue_refresh_token(user_id: str) -> str:
    exp = datetime.now(tz=UTC) + timedelta(days=30)
    return jwt.encode(
        {"sub": user_id, "exp": exp, "type": "refresh", "jti": str(uuid4())},
        SETTINGS.jwt_secret,
        algorithm="HS256",
    )


def decode_refresh_token(refresh_token: str) -> dict:
    payload = jwt.decode(refresh_token, SETTINGS.jwt_secret, algorithms=["HS256"])
    if payload.get("type") != "refresh":
        raise InvalidTokenError()
    if not payload.get("sub"):
        raise InvalidTokenError()
    return payload
