"""Sync service for Android data synchronization"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from config.database import SessionLocal
from models.sync_event import SyncEvent
from models.user import User
from repositories.sync_repository import SyncRepository

logger = logging.getLogger(__name__)


class SyncService:
    """Orchestrates idempotent data sync from Android devices"""

    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal
        self.sync_repo = SyncRepository(db_session)

    def sync(self, user_id: str, device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process a sync payload from Android device.
        
        1. Upsert all data idempotently (receipts, categories, shops, cards)
        2. Create SyncEvent record
        3. Update user's last_sync_at timestamp
        
        Returns count of accepted records per type.
        """
        try:
            logger.info("sync started user_id=%s device_id=%s", user_id, device_id)

            # Start sync
            sync_started_at = datetime.now(tz=UTC)

            # Upsert all data
            accepted_counts = self.sync_repo.upsert_payload(user_id, payload)

            # Create sync event record
            sync_event = SyncEvent(
                id=str(uuid4()),
                user_id=user_id,
                device_id=device_id,
                sync_started_at=sync_started_at,
                sync_completed_at=datetime.now(tz=UTC),
                status="success",
                receipts_count=accepted_counts.get("receipts", 0),
                line_items_count=accepted_counts.get("lineItems", 0),
                categories_count=accepted_counts.get("categories", 0),
                shops_count=accepted_counts.get("shops", 0),
                cards_count=accepted_counts.get("cards", 0),
                duplicates_count=accepted_counts.get("duplicates", 0),
            )
            self.db.add(sync_event)

            # Update user's last_sync_at
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_sync_at = sync_started_at
                self.db.add(user)

            self.db.commit()

            logger.info(
                "sync committed user_id=%s device_id=%s receipts=%s categories=%s shops=%s cards=%s duplicates=%s",
                user_id,
                device_id,
                accepted_counts.get("receipts", 0),
                accepted_counts.get("categories", 0),
                accepted_counts.get("shops", 0),
                accepted_counts.get("cards", 0),
                accepted_counts.get("duplicates", 0),
            )

            return {
                "accepted": {
                    "receipts": accepted_counts.get("receipts", 0),
                    "categories": accepted_counts.get("categories", 0),
                    "shops": accepted_counts.get("shops", 0),
                    "cards": accepted_counts.get("cards", 0),
                },
                "syncStats": {
                    "receipts": {
                        "received": accepted_counts.get("receipts", 0),
                        "inserted": accepted_counts.get("receiptsNew", 0),
                        "duplicates": accepted_counts.get("receiptsDuplicates", 0),
                    },
                    "categories": {
                        "received": accepted_counts.get("categories", 0),
                        "inserted": accepted_counts.get("categoriesNew", 0),
                        "duplicates": accepted_counts.get("categoriesDuplicates", 0),
                    },
                    "shops": {
                        "received": accepted_counts.get("shops", 0),
                        "inserted": accepted_counts.get("shopsNew", 0),
                        "duplicates": accepted_counts.get("shopsDuplicates", 0),
                    },
                    "cards": {
                        "received": accepted_counts.get("cards", 0),
                        "inserted": accepted_counts.get("cardsNew", 0),
                        "duplicates": accepted_counts.get("cardsDuplicates", 0),
                    },
                },
                "duplicates": accepted_counts.get("duplicates", 0),
                "lastSyncAt": sync_started_at.isoformat(),
            }
        except Exception:
            self.db.rollback()
            logger.exception("sync failed user_id=%s device_id=%s", user_id, device_id)
            raise
