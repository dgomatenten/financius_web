"""
Phase 4 — Auth view tests.

Covers the full auth flow: register → login → access protected endpoint
→ refresh → logout → revoked. Also verifies token cross-stack compatibility:
a JWT issued with the same JWT_SECRET (as the Flask stack uses) authenticates
on Django endpoints without any client-side changes.
"""
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import RefreshToken

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_access_token(user_id: str, ttl_seconds: int = 3600) -> str:
    exp = datetime.now(tz=UTC) + timedelta(seconds=ttl_seconds)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.JWT_SECRET, algorithm="HS256")


def _make_refresh_token(user_id: str, ttl_days: int = 30) -> str:
    import uuid
    exp = datetime.now(tz=UTC) + timedelta(days=ttl_days)
    return jwt.encode(
        {"sub": str(user_id), "exp": exp, "type": "refresh", "jti": str(uuid.uuid4())},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


# ── Register ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegisterView:
    def test_valid_registration(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/register", {"email": "new@test.com", "password": "pass1234"}, format="json")
        assert r.status_code == 201
        body = r.json()
        assert body["error"] is None
        assert body["data"]["user"]["email"] == "new@test.com"
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]
        assert body["data"]["expiresIn"] == settings.ACCESS_TOKEN_TTL_SECONDS

    def test_response_envelope(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/register", {"email": "env@test.com", "password": "pass1234"}, format="json")
        body = r.json()
        assert "data" in body
        assert "error" in body
        assert "meta" in body

    def test_duplicate_email_returns_409(self, api_client: APIClient, user: User) -> None:
        r = api_client.post("/api/v1/auth/register", {"email": user.email, "password": "pass1234"}, format="json")
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "DUPLICATE_EMAIL"

    def test_invalid_email_returns_400(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/register", {"email": "notanemail", "password": "pass1234"}, format="json")
        assert r.status_code == 400
        assert r.json()["error"] is not None

    def test_short_password_returns_400(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/register", {"email": "pw@test.com", "password": "abc"}, format="json")
        assert r.status_code == 400

    def test_missing_body_returns_400(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/register", {}, format="json")
        assert r.status_code == 400

    def test_register_creates_refresh_token_in_db(self, api_client: APIClient) -> None:
        api_client.post("/api/v1/auth/register", {"email": "db@test.com", "password": "pass1234"}, format="json")
        user = User.objects.get(email="db@test.com")
        assert RefreshToken.objects.filter(user=user).exists()

    def test_email_normalized_to_lowercase(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/register", {"email": "UPPER@Test.COM", "password": "pass1234"}, format="json")
        assert r.status_code == 201
        assert r.json()["data"]["user"]["email"] == "upper@test.com"


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoginView:
    def test_valid_login(self, api_client: APIClient, user: User) -> None:
        r = api_client.post("/api/v1/auth/login", {"email": user.email, "password": "testpassword123"}, format="json")
        assert r.status_code == 200
        body = r.json()
        assert body["error"] is None
        assert body["data"]["user"]["email"] == user.email
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]

    def test_wrong_password_returns_401(self, api_client: APIClient, user: User) -> None:
        r = api_client.post("/api/v1/auth/login", {"email": user.email, "password": "wrongpass"}, format="json")
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_unknown_email_returns_401(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/login", {"email": "ghost@test.com", "password": "pass1234"}, format="json")
        assert r.status_code == 401
        assert r.json()["error"] is not None

    def test_missing_fields_returns_400(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/login", {"email": "only@test.com"}, format="json")
        assert r.status_code == 400

    def test_login_response_envelope(self, api_client: APIClient, user: User) -> None:
        r = api_client.post("/api/v1/auth/login", {"email": user.email, "password": "testpassword123"}, format="json")
        body = r.json()
        assert "data" in body and "error" in body and "meta" in body


# ── Refresh ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRefreshView:
    def test_valid_refresh_returns_new_access_token(self, api_client: APIClient, user: User) -> None:
        refresh_token = _make_refresh_token(user.pk)
        RefreshToken.objects.create(user=user, token_hash=__import__("hashlib").sha256(refresh_token.encode()).hexdigest())
        r = api_client.post("/api/v1/auth/refresh", {"refreshToken": refresh_token}, format="json")
        assert r.status_code == 200
        body = r.json()
        assert body["error"] is None
        assert "accessToken" in body["data"]
        assert body["data"]["refreshToken"] == refresh_token  # refresh token is stable

    def test_refresh_backward_compat_aliases(self, api_client: APIClient, user: User) -> None:
        refresh_token = _make_refresh_token(user.pk)
        RefreshToken.objects.create(user=user, token_hash=__import__("hashlib").sha256(refresh_token.encode()).hexdigest())
        r = api_client.post("/api/v1/auth/refresh", {"refreshToken": refresh_token}, format="json")
        body = r.json()
        # Android clients parse top-level aliases too
        assert "accessToken" in body
        assert "refreshToken" in body
        assert "access_token" in body
        assert "refresh_token" in body

    def test_expired_refresh_token_returns_401(self, api_client: APIClient, user: User) -> None:
        expired = _make_refresh_token(user.pk, ttl_days=-1)
        r = api_client.post("/api/v1/auth/refresh", {"refreshToken": expired}, format="json")
        assert r.status_code == 401
        body = r.json()
        assert "data" in body and "error" in body and "meta" in body
        assert body["error"]["code"] == "TOKEN_EXPIRED"

    def test_access_token_as_refresh_returns_401(self, api_client: APIClient, user: User) -> None:
        access_token = _make_access_token(user.pk)
        r = api_client.post("/api/v1/auth/refresh", {"refreshToken": access_token}, format="json")
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "INVALID_TOKEN"

    def test_missing_token_returns_400(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/refresh", {}, format="json")
        assert r.status_code == 400

    def test_auto_heal_missing_db_record(self, api_client: APIClient, user: User) -> None:
        """Valid signed refresh token not in DB gets auto-relinked (Android token persistence edge-case)."""
        refresh_token = _make_refresh_token(user.pk)
        # Intentionally do NOT create a RefreshToken in DB
        r = api_client.post("/api/v1/auth/refresh", {"refreshToken": refresh_token}, format="json")
        assert r.status_code == 200
        assert r.json()["error"] is None
        # DB record should now exist after auto-heal
        import hashlib
        assert RefreshToken.objects.filter(
            user=user, token_hash=hashlib.sha256(refresh_token.encode()).hexdigest()
        ).exists()


# ── Logout ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogoutView:
    def test_valid_logout_deletes_refresh_token(self, api_client: APIClient, user: User) -> None:
        import hashlib
        refresh_token = _make_refresh_token(user.pk)
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        RefreshToken.objects.create(user=user, token_hash=token_hash)

        r = api_client.post("/api/v1/auth/logout", {"refreshToken": refresh_token}, format="json")
        assert r.status_code == 200
        assert r.json()["data"]["loggedOut"] is True
        assert not RefreshToken.objects.filter(token_hash=token_hash).exists()

    def test_logout_unknown_token_still_succeeds(self, api_client: APIClient, user: User) -> None:
        refresh_token = _make_refresh_token(user.pk)
        r = api_client.post("/api/v1/auth/logout", {"refreshToken": refresh_token}, format="json")
        assert r.status_code == 200
        assert r.json()["data"]["loggedOut"] is True

    def test_missing_token_returns_400(self, api_client: APIClient) -> None:
        r = api_client.post("/api/v1/auth/logout", {}, format="json")
        assert r.status_code == 400


# ── Protected endpoint authentication ─────────────────────────────────────────

@pytest.mark.django_db
class TestProtectedEndpointAuth:
    def test_valid_jwt_accesses_protected_endpoint(self, api_client: APIClient, user: User) -> None:
        token = _make_access_token(user.pk)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        r = api_client.get("/api/v1/receipts/")
        assert r.status_code == 200
        assert r.json()["error"] is None

    def test_no_token_returns_401_in_envelope(self, api_client: APIClient) -> None:
        r = api_client.get("/api/v1/receipts/")
        assert r.status_code == 401
        body = r.json()
        assert "data" in body and "error" in body and "meta" in body
        assert body["error"] is not None

    def test_expired_token_returns_401_in_envelope(self, api_client: APIClient, user: User) -> None:
        expired = _make_access_token(user.pk, ttl_seconds=-1)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired}")
        r = api_client.get("/api/v1/receipts/")
        assert r.status_code == 401
        body = r.json()
        assert "data" in body and "error" in body and "meta" in body
        assert body["error"] is not None

    def test_malformed_token_returns_401_in_envelope(self, api_client: APIClient) -> None:
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not.a.jwt")
        r = api_client.get("/api/v1/receipts/")
        assert r.status_code == 401
        body = r.json()
        assert "data" in body and "error" in body and "meta" in body

    def test_wrong_secret_token_returns_401(self, api_client: APIClient, user: User) -> None:
        exp = datetime.now(tz=UTC) + timedelta(hours=1)
        bad_token = jwt.encode({"sub": str(user.pk), "exp": exp}, "wrong-secret", algorithm="HS256")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {bad_token}")
        r = api_client.get("/api/v1/receipts/")
        assert r.status_code == 401


# ── Token cross-stack compatibility ───────────────────────────────────────────

@pytest.mark.django_db
class TestTokenCrossStackCompatibility:
    def test_flask_style_jwt_authenticates_on_django(self, api_client: APIClient, user: User) -> None:
        """
        A JWT issued by the Flask stack (same JWT_SECRET, same HS256 claim shape)
        must authenticate successfully on the Django stack without any client changes.
        This is the key invariant that allows the Android app to switch base URLs
        without re-authenticating.
        """
        exp = datetime.now(tz=UTC) + timedelta(seconds=3600)
        flask_style_token = jwt.encode(
            {"sub": str(user.pk), "exp": exp},
            settings.JWT_SECRET,
            algorithm="HS256",
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {flask_style_token}")
        r = api_client.get("/api/v1/receipts/")
        assert r.status_code == 200
        assert r.json()["error"] is None

    def test_end_to_end_flow(self, api_client: APIClient) -> None:
        """Register → access protected endpoint → refresh → logout → access denied."""
        # Register
        reg = api_client.post(
            "/api/v1/auth/register",
            {"email": "e2e@test.com", "password": "pass1234"},
            format="json",
        ).json()
        assert reg["error"] is None
        access_token = reg["data"]["accessToken"]
        refresh_token = reg["data"]["refreshToken"]

        # Access protected endpoint
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        r = api_client.get("/api/v1/receipts/")
        assert r.status_code == 200

        # Refresh
        api_client.credentials()  # clear auth header
        refresh_resp = api_client.post(
            "/api/v1/auth/refresh",
            {"refreshToken": refresh_token},
            format="json",
        ).json()
        assert refresh_resp["error"] is None
        new_access_token = refresh_resp["data"]["accessToken"]

        # New access token works
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access_token}")
        r = api_client.get("/api/v1/receipts/")
        assert r.status_code == 200

        # Logout
        api_client.credentials()
        logout_resp = api_client.post(
            "/api/v1/auth/logout",
            {"refreshToken": refresh_token},
            format="json",
        ).json()
        assert logout_resp["data"]["loggedOut"] is True
