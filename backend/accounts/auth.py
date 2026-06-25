import logging

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request: object) -> tuple | None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as err:
            raise AuthenticationFailed("Token expired") from err
        except jwt.InvalidTokenError as err:
            raise AuthenticationFailed("Invalid token") from err
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationFailed("User not found")
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as err:
            raise AuthenticationFailed("User not found") from err
        return (user, token)

    def authenticate_header(self, request: object) -> str:
        return "Bearer"
