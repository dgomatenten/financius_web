import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. Extends AbstractUser so Django handles password hashing,
    session auth, and admin. Extra fields match the legacy Flask `users` table.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    # Extended to 256 chars to accommodate wrapped werkzeug scrypt hashes (~170 chars)
    password = models.CharField(max_length=256)
    google_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.email


class RefreshToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "refresh_tokens"

    def __str__(self) -> str:
        return f"RefreshToken(user={self.user_id})"
