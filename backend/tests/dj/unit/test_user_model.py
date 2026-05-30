import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import RefreshToken

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email(self) -> None:
        user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="secret123",
        )
        assert user.pk is not None
        assert user.email == "alice@example.com"
        assert user.is_active is True
        assert user.check_password("secret123")

    def test_email_is_unique(self, user: User) -> None:
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="other",
                email=user.email,
                password="password",
            )

    def test_google_sub_is_nullable(self) -> None:
        user = User.objects.create_user(
            username="bob", email="bob@example.com", password="pw"
        )
        assert user.google_sub is None

    def test_google_sub_is_unique(self) -> None:
        User.objects.create_user(
            username="u1", email="u1@example.com", password="pw", google_sub="goog-123"
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="u2", email="u2@example.com", password="pw", google_sub="goog-123"
            )

    def test_last_sync_at_is_nullable(self, user: User) -> None:
        assert user.last_sync_at is None

    def test_str(self, user: User) -> None:
        assert str(user) == user.email

    def test_db_table(self) -> None:
        assert User._meta.db_table == "users"


@pytest.mark.django_db
class TestRefreshTokenModel:
    def test_create_token(self, user: User) -> None:
        token = RefreshToken.objects.create(user=user, token_hash="abc123hash")
        assert token.pk is not None
        assert token.user == user
        assert token.token_hash == "abc123hash"
        assert token.created_at is not None

    def test_cascade_delete(self, user: User) -> None:
        RefreshToken.objects.create(user=user, token_hash="hash1")
        RefreshToken.objects.create(user=user, token_hash="hash2")
        user_id = user.pk
        user.delete()
        assert RefreshToken.objects.filter(user_id=user_id).count() == 0

    def test_db_table(self) -> None:
        assert RefreshToken._meta.db_table == "refresh_tokens"
