from json import JSONDecodeError
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from config.settings import get_settings
from repositories.user_repository import UserRepository
from services.auth_tokens import issue_access_token, issue_refresh_token
from utils.exceptions import InvalidCredentialsError, ValidationError


GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def _fetch_google_claims(id_token: str) -> dict[str, Any]:
    query = urlencode({"id_token": id_token})
    url = f"{GOOGLE_TOKEN_INFO_URL}?{query}"
    with urlopen(url, timeout=5) as response:
        payload = response.read().decode("utf-8")
    import json

    return json.loads(payload)


class GoogleOAuthService:
    def __init__(self, db_session):
        self.user_repo = UserRepository(db_session)
        self.settings = get_settings()

    def login_with_google(self, id_token: str) -> dict[str, Any]:
        if not id_token:
            raise ValidationError("Google ID token is required")

        try:
            claims = _fetch_google_claims(id_token)
        except (HTTPError, URLError, TimeoutError, JSONDecodeError):
            raise ValidationError("Unable to verify Google ID token")

        google_sub = claims.get("sub")
        email = claims.get("email")
        audience = claims.get("aud")
        email_verified = claims.get("email_verified") in {"true", True}

        if not google_sub or not email:
            raise ValidationError("Google token missing required claims")

        if (
            self.settings.google_client_id != "replace-me"
            and audience != self.settings.google_client_id
        ):
            raise InvalidCredentialsError()

        if not email_verified:
            raise ValidationError("Google account email must be verified")

        user = self.user_repo.find_by_google_sub(google_sub)
        if not user:
            user = self.user_repo.find_by_email(email)
            if user and user.google_sub and user.google_sub != google_sub:
                raise InvalidCredentialsError()
            if user:
                user = self.user_repo.link_google_sub(user, google_sub)
            else:
                user = self.user_repo.create_user(
                    email=email,
                    password_hash=None,
                    google_sub=google_sub,
                )

        access_token = issue_access_token(user.id)
        refresh_token = issue_refresh_token(user.id)
        self.user_repo.save_refresh_token(user.id, refresh_token)

        return {
            "user": {"id": user.id, "email": user.email},
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": 3600,
        }
