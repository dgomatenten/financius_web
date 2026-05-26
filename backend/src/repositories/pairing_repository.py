"""Repository for pairing tokens"""

import hashlib
from datetime import datetime

from config.database import SessionLocal
from models.pairing_token import PairingToken


class PairingRepository:
    """Database access layer for pairing tokens"""

    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal

    def create_pairing_token(
        self, user_id: str, token: str, expires_at: datetime
    ) -> PairingToken:
        """
        Create a pairing token for a user.
        Token is hashed before storage for security.
        """
        from uuid import uuid4

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        pairing_token = PairingToken(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )
        self.db.add(pairing_token)
        self.db.commit()
        self.db.refresh(pairing_token)
        return pairing_token

    def validate_pairing_token(
        self, user_id: str, token: str
    ) -> PairingToken | None:
        """
        Validate a pairing token for a user.
        Returns the token if valid and not expired, None otherwise.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        pairing_token = (
            self.db.query(PairingToken)
            .filter(
                PairingToken.user_id == user_id, PairingToken.token_hash == token_hash
            )
            .first()
        )

        if not pairing_token:
            return None

        # Check if token is expired
        if pairing_token.expires_at < datetime.utcnow() or pairing_token.consumed_at is not None:
            return None

        return pairing_token

    def consume_pairing_token(self, pairing_token: PairingToken) -> PairingToken:
        pairing_token.consumed_at = datetime.utcnow()
        self.db.add(pairing_token)
        self.db.commit()
        self.db.refresh(pairing_token)
        return pairing_token
