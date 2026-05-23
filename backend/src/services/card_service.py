from datetime import datetime
from typing import Any
from uuid import uuid4

from config.database import SessionLocal
from models.master_data import PaymentCard
from utils.exceptions import ValidationError


class CardService:
    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal

    def list_cards(self, user_id: str) -> list[dict[str, Any]]:
        cards = (
            self.db.query(PaymentCard)
            .filter(PaymentCard.user_id == user_id)
            .order_by(PaymentCard.nickname.asc())
            .all()
        )
        return [
            {
                "id": card.id,
                "nickname": card.nickname,
                "cardType": card.card_type,
                "network": card.network,
                "colorHex": card.color_hex,
                "isActive": card.is_active,
            }
            for card in cards
        ]

    def create_card(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        nickname = (payload.get("nickname") or "").strip()
        card_type = (payload.get("cardType") or "").strip()
        if not nickname:
            raise ValidationError("nickname is required")
        if not card_type:
            raise ValidationError("cardType is required")

        card = PaymentCard(
            id=str(uuid4()),
            user_id=user_id,
            nickname=nickname,
            card_type=card_type,
            network=(payload.get("network") or "").strip() or None,
            color_hex=(payload.get("colorHex") or "").strip() or None,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return {
            "id": card.id,
            "nickname": card.nickname,
            "cardType": card.card_type,
            "network": card.network,
            "colorHex": card.color_hex,
            "isActive": card.is_active,
        }

    def deactivate_card(self, user_id: str, card_id: str) -> dict[str, Any]:
        card = (
            self.db.query(PaymentCard)
            .filter(PaymentCard.user_id == user_id, PaymentCard.id == card_id)
            .first()
        )
        if not card:
            raise ValidationError("card not found")

        card.is_active = False
        card.updated_at = datetime.utcnow()
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return {
            "id": card.id,
            "nickname": card.nickname,
            "cardType": card.card_type,
            "network": card.network,
            "colorHex": card.color_hex,
            "isActive": card.is_active,
        }
