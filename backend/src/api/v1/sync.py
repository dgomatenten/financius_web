"""Android device sync API endpoints"""

import json
import logging

from flask import Blueprint, jsonify, request

from api.envelope import ok
from config.database import SessionLocal
from config.settings import get_settings
from services.sync_service import SyncService
from utils.auth import get_current_user_id
from utils.exceptions import ValidationError


bp = Blueprint("sync", __name__)
logger = logging.getLogger(__name__)


def _sync_payload_preview(body: dict) -> dict:
    """Return a compact payload preview for logs to inspect what app sent."""
    def head(items: list, limit: int = 3) -> list:
        return items[:limit] if isinstance(items, list) else []

    receipts = body.get("receipts", []) or []
    categories = body.get("categories", []) or []
    shops = body.get("shops", []) or []
    cards = body.get("cards", []) or []

    return {
        "deviceId": body.get("deviceId"),
        "counts": {
            "receipts": len(receipts),
            "categories": len(categories),
            "shops": len(shops),
            "cards": len(cards),
        },
        "receiptsHead": [
            {
                "externalId": r.get("externalId"),
                "receiptDate": r.get("receiptDate") or r.get("date"),
                "currency": r.get("currency"),
                "total": r.get("total") or r.get("totalAmount"),
                "shopExternalId": r.get("shopExternalId") or r.get("shopId"),
                "categoryExternalId": r.get("categoryExternalId") or r.get("categoryId"),
                "paymentCardExternalId": (
                    r.get("paymentCardExternalId") or r.get("paymentCardId") or r.get("cardExternalId")
                ),
                "lineItemsCount": len(r.get("lineItems", []) or []),
            }
            for r in head(receipts)
            if isinstance(r, dict)
        ],
        "categoriesHead": [
            {"externalId": c.get("externalId"), "name": c.get("name")}
            for c in head(categories)
            if isinstance(c, dict)
        ],
        "shopsHead": [
            {"externalId": s.get("externalId"), "name": s.get("name"), "address": s.get("address") or s.get("location")}
            for s in head(shops)
            if isinstance(s, dict)
        ],
        "cardsHead": [
            {
                "externalId": c.get("externalId"),
                "nickname": c.get("nickname") or c.get("name"),
                "cardType": c.get("cardType"),
            }
            for c in head(cards)
            if isinstance(c, dict)
        ],
    }


@bp.post("")
def sync_payload() -> tuple:
    """
    Sync receipts, categories, shops, and cards from Android device.
    
    Request: {
        "deviceId": "device-123",
        "receipts": [...],
        "categories": [...],
        "shops": [...],
        "cards": [...]
    }
    
    Response: {
        "data": {
            "accepted": {receipts: n, categories: n, shops: n, cards: n},
            "lastSyncAt": "2026-05-17T...",
            "syncId": "sync-123"
        },
        "error": null
    }
    """
    user_id = get_current_user_id()
    settings = get_settings()

    if request.content_length and request.content_length > settings.sync_max_payload_bytes:
        max_mb = settings.sync_max_payload_bytes // (1024 * 1024)
        raise ValidationError(
            f"Request payload too large. Max is {max_mb}MB. Send sync in smaller batches."
        )

    body = request.get_json(silent=True) or {}

    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object")

    for key in ("receipts", "categories", "shops", "cards"):
        value = body.get(key, [])
        if value is None:
            continue
        if not isinstance(value, list):
            raise ValidationError(f"{key} must be an array")

    total_items = sum(len(body.get(key, []) or []) for key in ("receipts", "categories", "shops", "cards"))
    if total_items > settings.sync_max_items_per_request:
        raise ValidationError(
            "Sync payload has too many items. "
            f"Max {settings.sync_max_items_per_request} items per request. "
            "Upload in batches."
        )
    
    device_id = body.get("deviceId")
    if not device_id:
        raise ValidationError("deviceId is required")

    payload_preview = _sync_payload_preview(body)
    logger.info("sync payload preview=%s", json.dumps(payload_preview, ensure_ascii=True))

    logger.info(
        "sync request received user_id=%s device_id=%s items_total=%s",
        user_id,
        device_id,
        total_items,
    )
    
    db = SessionLocal()
    try:
        service = SyncService(db)
        data = service.sync(user_id, device_id, body)
        logger.info(
            "sync request completed user_id=%s device_id=%s accepted=%s duplicates=%s sync_stats=%s",
            user_id,
            device_id,
            data.get("accepted"),
            data.get("duplicates", 0),
            data.get("syncStats"),
        )
        return jsonify(ok(data)), 200
    except Exception:
        logger.exception("sync request failed user_id=%s device_id=%s", user_id, device_id)
        raise
    finally:
        db.close()


@bp.get("/status")
def sync_status() -> tuple:
    """
    Get the current user's last sync status.
    
    Response: {
        "data": {
            "lastSyncAt": "2026-05-17T..." or null,
            "status": "idle"
        },
        "error": null
    }
    """
    user_id = get_current_user_id()
    
    db = SessionLocal()
    try:
        from models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        
        return jsonify(ok({
            "lastSyncAt": user.last_sync_at.isoformat() if user and user.last_sync_at else None,
            "status": "idle"
        })), 200
    finally:
        db.close()
