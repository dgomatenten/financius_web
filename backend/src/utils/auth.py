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
        logger.warning("expired access token rejected — client must refresh")
        raise InvalidTokenError() from None
    except (jwt.DecodeError, jwt.InvalidTokenError):
        logger.warning("invalid access token decode failure")
        raise InvalidTokenError() from None
