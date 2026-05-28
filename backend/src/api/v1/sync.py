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


def _normalise_payload(body: dict) -> dict:
    """
    Normalise Financius Android field-name aliases into canonical web-side names.

    Original Financius Android app uses:
      transactions  → receipts
      accounts      → cards
      tags          → shops (some variants)
      transaction.accountId / transaction.account.id  → paymentCardId
      transaction.date (epoch ms) → receiptDate (ISO string)
      transaction.amount (negative cents) → total (positive float)
    """
    result = dict(body)

    # Top-level collection aliases
    if "transactions" in result and "receipts" not in result:
        result["receipts"] = result.pop("transactions")
    if "accounts" in result and "cards" not in result:
        result["cards"] = result.pop("accounts")
    if "tags" in result and "shops" not in result:
        result["tags"] = result.pop("shops")

    # Normalise per-receipt (transaction) field aliases
    normalised_receipts = []
    for r in result.get("receipts", []) or []:
        if not isinstance(r, dict):
            continue
        r = dict(r)

        # id → externalId
        if "externalId" not in r and "id" in r:
            r["externalId"] = r["id"]

        # date (epoch ms int) → receiptDate (ISO string)
        if "receiptDate" not in r and "date" in r:
            raw_date = r["date"]
            if isinstance(raw_date, (int, float)):
                from datetime import UTC, datetime
                # Epoch milliseconds (Android stores ms)
                r["receiptDate"] = datetime.fromtimestamp(raw_date / 1000, tz=UTC).isoformat()
            else:
                r["receiptDate"] = raw_date

        # amount (negative cents, expense) → total (positive float dollars)
        if "total" not in r and "totalAmount" not in r and "amount" in r:
            raw_amount = r.get("amount", 0)
            if isinstance(raw_amount, (int, float)):
                r["total"] = abs(raw_amount) / 100.0  # cents → dollars
            else:
                r["total"] = raw_amount

        # accountId → paymentCardId (Financius calls card an "account")
        if "paymentCardId" not in r and "paymentCardExternalId" not in r:
            account_id = r.get("accountId") or r.get("account_id")
            if not account_id:
                # Embedded account object: {"account": {"id": "...", "title": "..."}}
                account_obj = r.get("account") or r.get("paymentCard")
                if isinstance(account_obj, dict):
                    account_id = account_obj.get("id") or account_obj.get("externalId")
                    if not r.get("paymentCardId"):
                        r["paymentCardId"] = account_id
            else:
                r["paymentCardId"] = account_id

        # Embedded category object: {"category": {"id": "...", "title": "..."}}
        if "categoryId" not in r and "categoryExternalId" not in r:
            category_obj = r.get("category")
            if isinstance(category_obj, dict):
                r["categoryId"] = category_obj.get("id") or category_obj.get("externalId")

        # Category from line items: Android stores categoryId per line item,
        # not at receipt level. Use the first (or most common) line item categoryId.
        if "categoryId" not in r and "categoryExternalId" not in r:
            line_items = r.get("lineItems") or []
            for li in line_items:
                if isinstance(li, dict):
                    li_cat = li.get("categoryId") or li.get("categoryExternalId")
                    if li_cat:
                        r["categoryId"] = li_cat
                        break

        # Embedded shop/tag object: {"shop": {"id": "...", "name": "..."}}
        if "shopId" not in r and "shopExternalId" not in r:
            shop_obj = r.get("shop") or r.get("tag") or r.get("merchant")
            if isinstance(shop_obj, dict):
                r["shopId"] = shop_obj.get("id") or shop_obj.get("externalId")
                if not r.get("shopName"):
                    r["shopName"] = shop_obj.get("name") or shop_obj.get("title")

        # Normalise line item field aliases: qty→quantity, amount→unitPrice
        normalised_line_items = []
        for li in r.get("lineItems") or []:
            if not isinstance(li, dict):
                continue
            li = dict(li)
            if "quantity" not in li and "qty" in li:
                li["quantity"] = li.pop("qty")
            if "unitPrice" not in li and "amount" in li:
                li["unitPrice"] = li.pop("amount")
            normalised_line_items.append(li)
        r["lineItems"] = normalised_line_items

        normalised_receipts.append(r)

    result["receipts"] = normalised_receipts

    # Normalise per-account (card) aliases
    normalised_cards = []
    for c in result.get("cards", []) or []:
        if not isinstance(c, dict):
            continue
        c = dict(c)
        if "externalId" not in c and "id" in c:
            c["externalId"] = c["id"]
        if "nickname" not in c:
            c["nickname"] = c.get("title") or c.get("name") or ""
        if "cardType" not in c:
            c["cardType"] = c.get("type") or "credit"
        normalised_cards.append(c)
    result["cards"] = normalised_cards

    # Normalise per-category aliases
    normalised_categories = []
    for cat in result.get("categories", []) or []:
        if not isinstance(cat, dict):
            continue
        cat = dict(cat)
        if "externalId" not in cat and "id" in cat:
            cat["externalId"] = cat["id"]
        if "name" not in cat:
            cat["name"] = cat.get("title") or ""
        normalised_categories.append(cat)
    result["categories"] = normalised_categories

    # Normalise per-shop/tag aliases
    normalised_shops = []
    for s in result.get("shops", []) or []:
        if not isinstance(s, dict):
            continue
        s = dict(s)
        if "externalId" not in s and "id" in s:
            s["externalId"] = s["id"]
        if "name" not in s:
            s["name"] = s.get("title") or ""
        normalised_shops.append(s)
    result["shops"] = normalised_shops

    return result


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

    # Normalise Financius Android field-name aliases so both the original
    # Financius app and future app variants work without changes.
    body = _normalise_payload(body)

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

    # Log raw first receipt (all fields) so we can diagnose unknown field names from Android.
    top_keys = sorted(body.keys())
    raw_receipts = body.get("receipts") or []
    first_receipt_raw = raw_receipts[0] if raw_receipts else {}
    logger.info(
        "sync schema top_keys=%s first_receipt_raw=%s",
        top_keys,
        json.dumps(first_receipt_raw, ensure_ascii=True, default=str),
    )

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
