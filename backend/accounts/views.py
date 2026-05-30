import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from json import JSONDecodeError
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RefreshToken

User = get_user_model()
logger = logging.getLogger(__name__)


def _ok(data: Any, meta: dict | None = None) -> dict:
    return {"data": data, "error": None, "meta": meta or {}}


def _err(code: str, message: str) -> dict:
    return {"data": None, "error": {"code": code, "message": message}, "meta": {}}


def _hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def _issue_access_token(user_id: str, email: str = "") -> str:
    exp = datetime.now(tz=UTC) + timedelta(seconds=settings.ACCESS_TOKEN_TTL_SECONDS)
    return jwt.encode({"sub": str(user_id), "email": email, "exp": exp}, settings.JWT_SECRET, algorithm="HS256")


def _issue_refresh_token(user_id: str) -> str:
    exp = datetime.now(tz=UTC) + timedelta(days=30)
    return jwt.encode(
        {"sub": str(user_id), "exp": exp, "type": "refresh", "jti": str(uuid.uuid4())},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def _save_refresh_token(user: Any, token: str) -> None:
    token_hash = _hash_token(token)
    RefreshToken.objects.get_or_create(user=user, token_hash=token_hash)


def _issue_tokens(user: Any) -> dict:
    access_token = _issue_access_token(user.pk, user.email)
    refresh_token = _issue_refresh_token(user.pk)
    _save_refresh_token(user, refresh_token)
    return {
        "user": {"id": str(user.pk), "email": user.email},
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresIn": settings.ACCESS_TOKEN_TTL_SECONDS,
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        if not email or "@" not in email:
            return Response(_err("VALIDATION_ERROR", "Invalid email format"), status=400)
        if not password or len(password) < 6:
            return Response(_err("VALIDATION_ERROR", "Password must be at least 6 characters"), status=400)
        if User.objects.filter(email=email).exists():
            return Response(_err("DUPLICATE_EMAIL", "Email already registered"), status=409)
        user = User.objects.create_user(username=email, email=email, password=password)
        logger.info("register user_id=%s email=%s", user.pk, email)
        return Response(_ok(_issue_tokens(user)), status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""
        if not email or not password:
            return Response(_err("VALIDATION_ERROR", "Email and password are required"), status=400)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(_err("INVALID_CREDENTIALS", "Invalid credentials"), status=401)
        if not user.check_password(password):
            return Response(_err("INVALID_CREDENTIALS", "Invalid credentials"), status=401)
        logger.info("login user_id=%s email=%s", user.pk, email)
        return Response(_ok(_issue_tokens(user)))


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        id_token = (request.data.get("idToken") or "").strip()
        if not id_token:
            return Response(_err("VALIDATION_ERROR", "Google ID token is required"), status=400)
        try:
            query = urlencode({"id_token": id_token})
            with urlopen(f"https://oauth2.googleapis.com/tokeninfo?{query}", timeout=5) as resp:
                claims = json.loads(resp.read().decode())
        except (HTTPError, URLError, TimeoutError, JSONDecodeError):
            return Response(_err("VALIDATION_ERROR", "Unable to verify Google ID token"), status=400)

        google_sub = claims.get("sub")
        email = (claims.get("email") or "").lower()
        if not google_sub or not email:
            return Response(_err("VALIDATION_ERROR", "Google token missing required claims"), status=400)
        if claims.get("email_verified") not in {True, "true"}:
            return Response(_err("VALIDATION_ERROR", "Google account email must be verified"), status=400)

        google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", "replace-me")
        if google_client_id != "replace-me" and claims.get("aud") != google_client_id:
            return Response(_err("INVALID_CREDENTIALS", "Invalid token audience"), status=401)

        user = User.objects.filter(google_sub=google_sub).first()
        if not user:
            user = User.objects.filter(email=email).first()
            if user:
                if user.google_sub and user.google_sub != google_sub:
                    return Response(_err("INVALID_CREDENTIALS", "Invalid credentials"), status=401)
                user.google_sub = google_sub
                user.save(update_fields=["google_sub"])
            else:
                user = User.objects.create_user(username=email, email=email, google_sub=google_sub)
                user.set_unusable_password()
                user.save(update_fields=["password"])

        logger.info("google_login user_id=%s email=%s", user.pk, email)
        return Response(_ok(_issue_tokens(user)))


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        token = (request.data.get("refreshToken") or "").strip()
        if not token:
            return Response(_err("VALIDATION_ERROR", "Refresh token is required"), status=400)
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return Response(_err("TOKEN_EXPIRED", "Refresh token expired"), status=401)
        except jwt.InvalidTokenError:
            return Response(_err("INVALID_TOKEN", "Invalid refresh token"), status=401)
        if payload.get("type") != "refresh":
            return Response(_err("INVALID_TOKEN", "Not a refresh token"), status=401)
        user_id = payload.get("sub")
        if not user_id:
            return Response(_err("INVALID_TOKEN", "Token missing sub claim"), status=401)

        token_hash = _hash_token(token)
        if not RefreshToken.objects.filter(token_hash=token_hash).exists():
            try:
                user = User.objects.get(pk=user_id)
                logger.warning("refresh token auto-heal for user_id=%s", user_id)
                _save_refresh_token(user, token)
            except User.DoesNotExist:
                logger.warning("refresh token fallback without user row for sub=%s", user_id)

        try:
            _email = User.objects.get(pk=user_id).email
        except User.DoesNotExist:
            _email = ""
        access_token = _issue_access_token(user_id, _email)
        data = {
            "accessToken": access_token,
            "refreshToken": token,
            "expiresIn": settings.ACCESS_TOKEN_TTL_SECONDS,
        }
        # Backward-compatible top-level aliases some Android Retrofit clients parse
        response_body = _ok(data)
        response_body.update({
            "accessToken": access_token,
            "refreshToken": token,
            "expiresIn": settings.ACCESS_TOKEN_TTL_SECONDS,
            "access_token": access_token,
            "refresh_token": token,
            "expires_in": settings.ACCESS_TOKEN_TTL_SECONDS,
        })
        return Response(response_body)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        token = (request.data.get("refreshToken") or "").strip()
        if not token:
            return Response(_err("VALIDATION_ERROR", "Refresh token is required"), status=400)
        token_hash = _hash_token(token)
        RefreshToken.objects.filter(token_hash=token_hash).delete()
        return Response(_ok({"loggedOut": True}))
