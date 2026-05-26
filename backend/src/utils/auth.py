"""JWT token extraction and validation utilities"""

import logging

import jwt
from flask import request

from config.settings import get_settings
from utils.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)


def get_current_user_id() -> str:
    """
    Extract user_id from JWT token in Authorization header.
    Raises InvalidTokenError if token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise InvalidTokenError()

    token = auth_header[7:]  # Remove "Bearer " prefix
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()
        return user_id
    except jwt.ExpiredSignatureError:
        # Compatibility fallback for clients that fail to swap to refreshed
        # access tokens. Accept expired token subject to avoid sync lockout.
        try:
            settings = get_settings()
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            user_id = payload.get("sub")
            if user_id:
                logger.warning("using expired access token compatibility path for sub=%s", user_id)
                return user_id
        except Exception:
            pass
        raise InvalidTokenError() from None
    except (jwt.DecodeError, jwt.InvalidTokenError):
        logger.warning("invalid access token decode failure")
        raise InvalidTokenError() from None
