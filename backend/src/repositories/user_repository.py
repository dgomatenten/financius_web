from typing import Optional

from config.database import SessionLocal
from models.user import RefreshToken, User
from services.auth_tokens import hash_token


class UserRepository:
    """Database access layer for User model"""

    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal

    def create_user(
        self,
        email: str,
        password_hash: Optional[str] = None,
        google_sub: Optional[str] = None,
    ) -> User:
        """Create a new user in the database"""
        user = User(
            id=email,  # Use email as ID for simplicity
            email=email,
            password_hash=password_hash,
            google_sub=google_sub,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def link_google_sub(self, user: User, google_sub: str) -> User:
        user.google_sub = google_sub
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def find_by_google_sub(self, google_sub: str) -> Optional[User]:
        """Find user by Google OAuth subject"""
        return self.db.query(User).filter(User.google_sub == google_sub).first()

    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def save_refresh_token(self, user_id: str, refresh_token: str) -> RefreshToken:
        token_hash = hash_token(refresh_token)
        token = RefreshToken(id=token_hash, user_id=user_id, token_hash=token_hash)
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def find_refresh_token(self, refresh_token: str) -> Optional[RefreshToken]:
        token_hash = hash_token(refresh_token)
        return self.db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    def delete_refresh_token(self, refresh_token: str) -> None:
        token = self.find_refresh_token(refresh_token)
        if token:
            self.db.delete(token)
            self.db.commit()

    def delete_refresh_tokens_for_user(self, user_id: str) -> None:
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
        self.db.commit()
