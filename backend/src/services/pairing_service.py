"""Pairing service for Android device QR code authentication"""

import secrets
from datetime import UTC, datetime, timedelta

from config.settings import get_settings
from repositories.pairing_repository import PairingRepository
from utils.exceptions import InvalidTokenError


class PairingService:
    """Manages QR code pairing tokens for Android devices"""

    def __init__(self, db_session=None):
        self.pairing_repo = PairingRepository(db_session)
        self.settings = get_settings()

    def generate_pairing_token(self, user_id: str) -> dict[str, str]:
        """
        Generate a new pairing token and store it in database.
        Token is embedded in QR code that Android scans.
        
        Returns:
        {
            "serverBaseUrl": "https://api.example.com",
            "pairingToken": "<random-token>",
            "expiresAt": "2026-05-17T11:35:00Z"
        }
        """
        # Generate random token
        token = secrets.token_urlsafe(24)

        # Calculate expiry
        expires_at = datetime.now(tz=UTC) + timedelta(
            seconds=self.settings.qr_pairing_token_ttl_seconds
        )

        # Store in database (hashed)
        self.pairing_repo.create_pairing_token(user_id, token, expires_at)

        return {
            "serverBaseUrl": self.settings.api_base_url,
            "pairingToken": token,
            "expiresAt": expires_at.isoformat(),
        }

    def validate_pairing_token(self, user_id: str, token: str) -> None:
        """
        Validate a pairing token for a user.
        Raises InvalidTokenError if token is invalid or expired.
        """
        valid_token = self.pairing_repo.validate_pairing_token(user_id, token)
        if not valid_token:
            raise InvalidTokenError()
        self.pairing_repo.consume_pairing_token(valid_token)
