"""
Django REST Framework views for all ledger endpoints.

Preserves exact request/response shapes from the Flask blueprints so that
Android Retrofit clients can switch URLs without any client-side changes.
"""
from __future__ import annotations

import hashlib
import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AmortizationRule,
    Budget,
    Category,
    CategoryMapping,
    PairingToken,
    PaymentCard,
    Receipt,
    ReceiptLineItem,
    RecurringExpenseOccurrence,
    RecurringExpenseTemplate,
    Shop,
    SyncEvent,
)

User = get_user_model()
logger = logging.getLogger(__name__)

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


# ── Response helpers ──────────────────────────────────────────────────────────

def _ok(data: Any, meta: dict | None = None) -> dict:
    return {"data": data, "error": None, "meta": meta or {}}


def _err(code: str, message: str) -> dict:
    return {"data": None, "error": {"code": code, "message": message}, "meta": {}}


# ── Date parsing ──────────────────────────────────────────────────────────────

def _parse_dt(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=UTC)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, AttributeError):
        return datetime.now(tz=UTC)


def _parse_dt_filter(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


# ── Receipt serialization ─────────────────────────────────────────────────────

def _receipt_dict(receipt: Receipt, include_lines: bool = False) -> dict:
    shop_name = receipt.shop.name if receipt.shop_id and hasattr(receipt, "shop") and receipt.shop else None
    data: dict = {
        "id": str(receipt.id),
        "receiptDate": receipt.receipt_date.isoformat(),
        "shopId": str(receipt.shop_id) if receipt.shop_id else None,
        "shopName": shop_name,
        "totalAmount": receipt.total_amount,
        "currency": receipt.currency,
        "categoryId": str(receipt.category_id) if receipt.category_id else None,
        "note": receipt.note,
        "paymentCardId": str(receipt.payment_card_id) if receipt.payment_card_id else None,
    }
    if include_lines:
        data["lineItems"] = [
            {
                "name": li.name,
                "quantity": li.quantity,
                "unitPrice": li.unit_price,
                "lineTotal": li.line_total,
            }
            for li in receipt.line_items.all()
        ]
    return data


# ── ReceiptViewSet ────────────────────────────────────────────────────────────

class ReceiptListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = Receipt.objects.filter(user=request.user).select_related("shop")
        params = request.query_params

        if currency := params.get("currency"):
            qs = qs.filter(currency=currency)
        if category_id := params.get("categoryId"):
            qs = qs.filter(category_id=category_id)
        if from_date := params.get("fromDate"):
            try:
                qs = qs.filter(receipt_date__gte=_parse_dt_filter(from_date))
            except ValueError:
                return Response(_err("VALIDATION_ERROR", "Invalid fromDate format"), status=400)
        if to_date := params.get("toDate"):
            try:
                qs = qs.filter(receipt_date__lte=_parse_dt_filter(to_date))
            except ValueError:
                return Response(_err("VALIDATION_ERROR", "Invalid toDate format"), status=400)
        if search := params.get("search"):
            qs = qs.filter(note__icontains=search)

        try:
            page = max(int(params.get("page", 1)), 1)
            page_size = max(min(int(params.get("pageSize", 20)), 100), 1)
        except (ValueError, TypeError):
            page, page_size = 1, 20

        offset = (page - 1) * page_size
        receipts = qs.order_by("-receipt_date")[offset : offset + page_size]
        items = [_receipt_dict(r) for r in receipts]
        logger.info("receipts.list user=%s filters=%s returned=%s", request.user.id, dict(params), len(items))
        return Response(_ok({"items": items}))


class ReceiptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, receipt_id: str) -> Response:
        try:
            receipt = Receipt.objects.select_related("shop").get(pk=receipt_id, user=request.user)
        except Receipt.DoesNotExist:
            return Response(_err("NOT_FOUND", "Receipt not found"), status=404)
        return Response(_ok(_receipt_dict(receipt, include_lines=True)))

    def patch(self, request: Request, receipt_id: str) -> Response:
        try:
            receipt = Receipt.objects.get(pk=receipt_id, user=request.user)
        except Receipt.DoesNotExist:
            return Response(_err("NOT_FOUND", "Receipt not found"), status=404)

        body = request.data or {}
        allowed = {"categoryId", "paymentCardId", "note"}
        unknown = [k for k in body if k not in allowed]
        if unknown:
            return Response(_err("VALIDATION_ERROR", "Unsupported receipt update fields"), status=400)

        if "categoryId" in body:
            receipt.category_id = body["categoryId"] or None
        if "paymentCardId" in body:
            receipt.payment_card_id = body["paymentCardId"] or None
        if "note" in body:
            receipt.note = body["note"]
        receipt.save()

        receipt = Receipt.objects.select_related("shop").get(pk=receipt_id)
        return Response(_ok(_receipt_dict(receipt, include_lines=True)))


class ReceiptBulkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        body = request.data or {}
        operation = body.get("operation", "")
        ids = body.get("receiptIds", [])
        if not ids:
            return Response(_ok({"affected": 0}))

        receipts = list(Receipt.objects.filter(user=request.user, pk__in=ids))
        if not receipts:
            return Response(_ok({"affected": 0}))

        if operation == "recategorize":
            category_id = body.get("categoryId")
            Receipt.objects.filter(user=request.user, pk__in=ids).update(category_id=category_id)
        elif operation == "reassign_card":
            card_id = body.get("paymentCardId")
            Receipt.objects.filter(user=request.user, pk__in=ids).update(payment_card_id=card_id)
        elif operation == "delete":
            ReceiptLineItem.objects.filter(receipt__in=receipts).delete()
            Receipt.objects.filter(user=request.user, pk__in=ids).delete()
        else:
            return Response(_err("VALIDATION_ERROR", f"Unknown operation: {operation}"), status=400)

        return Response(_ok({"affected": len(receipts)}))


class ReceiptAmazonImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        return Response(_ok({"imported": 0, "message": "Amazon import not yet implemented"}))


# ── Sync ──────────────────────────────────────────────────────────────────────

def _normalise_sync_payload(body: dict) -> dict:
    """Port of Flask sync.py _normalise_payload — maps Financius Android field aliases."""
    result = dict(body)

    if "transactions" in result and "receipts" not in result:
        result["receipts"] = result.pop("transactions")
    if "accounts" in result and "cards" not in result:
        result["cards"] = result.pop("accounts")
    if "tags" in result and "shops" not in result:
        result["shops"] = result.pop("tags")

    normalised_receipts = []
    for r in result.get("receipts", []) or []:
        if not isinstance(r, dict):
            continue
        r = dict(r)

        if "externalId" not in r and "id" in r:
            r["externalId"] = r["id"]

        if "receiptDate" not in r and "date" in r:
            raw_date = r["date"]
            if isinstance(raw_date, (int, float)):
                r["receiptDate"] = datetime.fromtimestamp(raw_date / 1000, tz=UTC).isoformat()
            else:
                r["receiptDate"] = raw_date

        if "total" not in r and "totalAmount" not in r and "amount" in r:
            raw = r.get("amount", 0)
            r["total"] = abs(raw) / 100.0 if isinstance(raw, (int, float)) else raw

        if "paymentCardId" not in r and "paymentCardExternalId" not in r:
            account_id = r.get("accountId") or r.get("account_id")
            if not account_id:
                account_obj = r.get("account") or r.get("paymentCard")
                if isinstance(account_obj, dict):
                    account_id = account_obj.get("id") or account_obj.get("externalId")
            if account_id:
                r["paymentCardId"] = account_id

        if "categoryId" not in r and "categoryExternalId" not in r:
            cat_obj = r.get("category")
            if isinstance(cat_obj, dict):
                r["categoryId"] = cat_obj.get("id") or cat_obj.get("externalId")

        if "categoryId" not in r and "categoryExternalId" not in r:
            for li in r.get("lineItems") or []:
                if isinstance(li, dict):
                    li_cat = li.get("categoryId") or li.get("categoryExternalId")
                    if li_cat:
                        r["categoryId"] = li_cat
                        break

        if "shopId" not in r and "shopExternalId" not in r:
            shop_obj = r.get("shop") or r.get("tag") or r.get("merchant")
            if isinstance(shop_obj, dict):
                r["shopId"] = shop_obj.get("id") or shop_obj.get("externalId")
                if not r.get("shopName"):
                    r["shopName"] = shop_obj.get("name") or shop_obj.get("title")

        normalised_lines = []
        for li in r.get("lineItems") or []:
            if not isinstance(li, dict):
                continue
            li = dict(li)
            if "quantity" not in li and "qty" in li:
                li["quantity"] = li.pop("qty")
            if "unitPrice" not in li and "amount" in li:
                li["unitPrice"] = li.pop("amount")
            normalised_lines.append(li)
        r["lineItems"] = normalised_lines
        normalised_receipts.append(r)
    result["receipts"] = normalised_receipts

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


def _upsert_categories(user: Any, categories: list[dict]) -> dict[str, int]:
    accepted = duplicates = 0
    for cat in categories:
        if not isinstance(cat, dict):
            continue
        ext_id = cat.get("externalId")
        if not ext_id:
            continue
        obj, created = Category.objects.get_or_create(
            user=user, external_id=str(ext_id),
            defaults={"name": cat.get("name", "")},
        )
        if created:
            accepted += 1
        else:
            Category.objects.filter(pk=obj.pk).update(name=cat.get("name", obj.name))
            accepted += 1
            duplicates += 1
    return {"accepted": accepted, "new": accepted - duplicates, "duplicates": duplicates}


def _upsert_shops(user: Any, shops: list[dict]) -> dict[str, int]:
    accepted = duplicates = 0
    for s in shops:
        if not isinstance(s, dict):
            continue
        ext_id = s.get("externalId")
        if not ext_id:
            continue
        obj, created = Shop.objects.get_or_create(
            user=user, external_id=str(ext_id),
            defaults={"name": s.get("name", ""), "address": s.get("address")},
        )
        if created:
            accepted += 1
        else:
            Shop.objects.filter(pk=obj.pk).update(
                name=s.get("name", obj.name), address=s.get("address", obj.address)
            )
            accepted += 1
            duplicates += 1
    return {"accepted": accepted, "new": accepted - duplicates, "duplicates": duplicates}


def _upsert_cards(user: Any, cards: list[dict]) -> dict[str, int]:
    accepted = duplicates = 0
    for c in cards:
        if not isinstance(c, dict):
            continue
        ext_id = c.get("externalId")
        if not ext_id:
            continue
        obj, created = PaymentCard.objects.get_or_create(
            user=user, external_id=str(ext_id),
            defaults={"nickname": c.get("nickname", ""), "card_type": c.get("cardType", "credit")},
        )
        if created:
            accepted += 1
        else:
            PaymentCard.objects.filter(pk=obj.pk).update(
                nickname=c.get("nickname", obj.nickname),
                card_type=c.get("cardType", obj.card_type),
            )
            accepted += 1
            duplicates += 1
    return {"accepted": accepted, "new": accepted - duplicates, "duplicates": duplicates}


def _resolve_shop(user: Any, receipt: dict) -> Any:
    shop_db_id = receipt.get("shopDbId") or receipt.get("shop_id")
    if shop_db_id:
        return Shop.objects.filter(pk=str(shop_db_id), user=user).first()

    ext_id = receipt.get("shopExternalId") or receipt.get("shopId")
    if ext_id:
        shop = Shop.objects.filter(user=user, external_id=str(ext_id)).first()
        if shop:
            return shop
        name = receipt.get("shopName") or receipt.get("merchant") or str(ext_id)
        logger.info("auto-creating stub shop ext_id=%s name=%s user=%s", ext_id, name, user.id)
        shop, _ = Shop.objects.get_or_create(
            user=user, external_id=str(ext_id), defaults={"name": str(name)}
        )
        return shop

    name = receipt.get("shopName") or receipt.get("merchant")
    if name:
        shop = Shop.objects.filter(user=user, name=str(name)).first()
        if shop:
            return shop
        logger.info("auto-creating stub shop by name=%s user=%s", name, user.id)
        shop = Shop.objects.create(user=user, name=str(name))
        return shop

    return None


def _resolve_category(user: Any, receipt: dict) -> Any:
    ext_id = receipt.get("categoryExternalId") or receipt.get("categoryId")
    if not ext_id:
        return None
    cat = Category.objects.filter(user=user, external_id=str(ext_id)).first()
    if cat:
        return cat
    name = receipt.get("categoryName") or str(ext_id)
    logger.info("auto-creating stub category ext_id=%s name=%s user=%s", ext_id, name, user.id)
    cat, _ = Category.objects.get_or_create(
        user=user, external_id=str(ext_id), defaults={"name": str(name)}
    )
    return cat


def _resolve_card(user: Any, receipt: dict) -> Any:
    ext_id = (
        receipt.get("paymentCardExternalId")
        or receipt.get("paymentCardId")
        or receipt.get("cardExternalId")
        or receipt.get("cardId")
    )
    if not ext_id:
        return None
    card = PaymentCard.objects.filter(user=user, external_id=str(ext_id)).first()
    if card:
        return card
    name = receipt.get("paymentCardName") or receipt.get("cardName") or str(ext_id)
    logger.info("auto-creating stub card ext_id=%s nickname=%s user=%s", ext_id, name, user.id)
    card, _ = PaymentCard.objects.get_or_create(
        user=user, external_id=str(ext_id),
        defaults={"nickname": str(name), "card_type": "credit"},
    )
    return card


def _upsert_receipts(user: Any, receipts: list[dict]) -> dict[str, int]:
    accepted = duplicates = line_items_count = 0
    for r in receipts:
        if not isinstance(r, dict):
            continue
        ext_id = r.get("externalId")
        if not ext_id:
            continue

        shop = _resolve_shop(user, r)
        category = _resolve_category(user, r)
        card = _resolve_card(user, r)

        receipt_date = _parse_dt(r.get("receiptDate") or r.get("date"))
        total = r.get("total", r.get("totalAmount", 0)) or 0

        existing = Receipt.objects.filter(user=user, external_id=str(ext_id)).first()
        if existing:
            updates: dict = {"receipt_date": receipt_date, "currency": r.get("currency", existing.currency)}
            if shop:
                updates["shop"] = shop
            if category:
                updates["category"] = category
            if card:
                updates["payment_card"] = card
            Receipt.objects.filter(pk=existing.pk).update(**updates)
            duplicates += 1
        else:
            receipt = Receipt.objects.create(
                user=user,
                external_id=str(ext_id),
                shop=shop,
                category=category,
                payment_card=card,
                receipt_date=receipt_date,
                currency=r.get("currency", "USD"),
                total_amount=float(total),
            )
            for li in r.get("lineItems") or []:
                if not isinstance(li, dict):
                    continue
                qty = li.get("quantity", 1)
                unit_price = li.get("unitPrice", 0)
                ReceiptLineItem.objects.create(
                    receipt=receipt,
                    name=li.get("name", ""),
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=li.get("lineTotal", float(qty) * float(unit_price)),
                )
                line_items_count += 1
        accepted += 1
    return {
        "accepted": accepted,
        "new": accepted - duplicates,
        "duplicates": duplicates,
        "lineItems": line_items_count,
    }


class SyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user = request.user
        content_length = request.META.get("CONTENT_LENGTH")
        if content_length and int(content_length) > settings.SYNC_MAX_PAYLOAD_BYTES:
            max_mb = settings.SYNC_MAX_PAYLOAD_BYTES // (1024 * 1024)
            return Response(_err("PAYLOAD_TOO_LARGE", f"Max is {max_mb}MB"), status=413)

        body = request.data if isinstance(request.data, dict) else {}
        if not isinstance(body, dict):
            return Response(_err("VALIDATION_ERROR", "Request body must be a JSON object"), status=400)

        body = _normalise_sync_payload(body)
        device_id = body.get("deviceId")
        if not device_id:
            return Response(_err("VALIDATION_ERROR", "deviceId is required"), status=400)

        total_items = sum(
            len(body.get(k, []) or []) for k in ("receipts", "categories", "shops", "cards")
        )
        if total_items > settings.SYNC_MAX_ITEMS_PER_REQUEST:
            return Response(
                _err("PAYLOAD_TOO_LARGE", f"Max {settings.SYNC_MAX_ITEMS_PER_REQUEST} items per request"),
                status=413,
            )

        logger.info("sync request user=%s device=%s items=%s", user.id, device_id, total_items)
        sync_started_at = datetime.now(tz=UTC)

        with transaction.atomic():
            cat_result = _upsert_categories(user, body.get("categories", []) or [])
            shop_result = _upsert_shops(user, body.get("shops", []) or [])
            card_result = _upsert_cards(user, body.get("cards", []) or [])
            receipt_result = _upsert_receipts(user, body.get("receipts", []) or [])

            SyncEvent.objects.create(
                user=user,
                device_id=str(device_id),
                sync_started_at=sync_started_at,
                sync_completed_at=datetime.now(tz=UTC),
                status="success",
                receipts_count=receipt_result["accepted"],
                line_items_count=receipt_result["lineItems"],
                categories_count=cat_result["accepted"],
                shops_count=shop_result["accepted"],
                cards_count=card_result["accepted"],
                duplicates_count=receipt_result["duplicates"] + cat_result["duplicates"]
                + shop_result["duplicates"] + card_result["duplicates"],
            )
            User.objects.filter(pk=user.pk).update(last_sync_at=sync_started_at)

        data = {
            "accepted": {
                "receipts": receipt_result["accepted"],
                "categories": cat_result["accepted"],
                "shops": shop_result["accepted"],
                "cards": card_result["accepted"],
            },
            "syncStats": {
                "receipts": {
                    "received": receipt_result["accepted"],
                    "inserted": receipt_result["new"],
                    "duplicates": receipt_result["duplicates"],
                },
                "categories": {
                    "received": cat_result["accepted"],
                    "inserted": cat_result["new"],
                    "duplicates": cat_result["duplicates"],
                },
                "shops": {
                    "received": shop_result["accepted"],
                    "inserted": shop_result["new"],
                    "duplicates": shop_result["duplicates"],
                },
                "cards": {
                    "received": card_result["accepted"],
                    "inserted": card_result["new"],
                    "duplicates": card_result["duplicates"],
                },
            },
            "lastSyncAt": sync_started_at.isoformat(),
        }
        logger.info(
            "sync complete user=%s device=%s accepted=%s duplicates=%s",
            user.id, device_id,
            data["accepted"],
            receipt_result["duplicates"] + cat_result["duplicates"]
            + shop_result["duplicates"] + card_result["duplicates"],
        )
        return Response(_ok(data))


class SyncStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        last_sync_at = user.last_sync_at
        return Response(_ok({
            "lastSyncAt": last_sync_at.isoformat() if last_sync_at else None,
            "status": "idle",
        }))


# ── Category ──────────────────────────────────────────────────────────────────

def _category_dict(cat: Category) -> dict:
    return {
        "id": str(cat.id),
        "name": cat.name,
        "parentId": str(cat.parent_id) if cat.parent_id else None,
        "displayOrder": cat.display_order,
        "isEngel": cat.is_engel,
        "needsWants": cat.needs_wants,
        "isHousing": cat.is_housing,
        "isFixedExpense": cat.is_fixed_expense,
        "children": [],
    }


def _build_category_tree(categories: list[Category]) -> list[dict]:
    nodes = {str(cat.id): _category_dict(cat) for cat in categories}
    roots: list[dict] = []
    for cat in categories:
        node = nodes[str(cat.id)]
        parent_id = str(cat.parent_id) if cat.parent_id else None
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


class CategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        cats = list(
            Category.objects.filter(user=request.user, is_deleted=False)
            .order_by("display_order", "name")
        )
        return Response(_ok(_build_category_tree(cats)))

    def post(self, request: Request) -> Response:
        body = request.data or {}
        name = (body.get("name") or "").strip()
        if not name:
            return Response(_err("VALIDATION_ERROR", "name is required"), status=400)

        parent_id = body.get("parentId")
        parent = None
        if parent_id:
            parent = Category.objects.filter(pk=parent_id, user=request.user, is_deleted=False).first()
            if not parent:
                return Response(_err("VALIDATION_ERROR", "parentId is invalid"), status=400)

        cat = Category.objects.create(
            user=request.user,
            name=name,
            parent=parent,
            display_order=int(body.get("displayOrder") or 0),
            is_engel=bool(body.get("isEngel", False)),
            needs_wants=str(body.get("needsWants") or "needs"),
            is_housing=bool(body.get("isHousing", False)),
            is_fixed_expense=bool(body.get("isFixedExpense", False)),
        )
        return Response(_ok(_category_dict(cat)), status=201)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, category_id: str) -> Response:
        try:
            cat = Category.objects.get(pk=category_id, user=request.user, is_deleted=False)
        except Category.DoesNotExist:
            return Response(_err("NOT_FOUND", "Category not found"), status=404)

        body = request.data or {}
        if "name" in body:
            name = (body["name"] or "").strip()
            if not name:
                return Response(_err("VALIDATION_ERROR", "name cannot be empty"), status=400)
            cat.name = name
        if "parentId" in body:
            pid = body["parentId"]
            if pid == str(cat.id):
                return Response(_err("VALIDATION_ERROR", "Category cannot be its own parent"), status=400)
            if pid:
                parent = Category.objects.filter(pk=pid, user=request.user, is_deleted=False).first()
                if not parent:
                    return Response(_err("VALIDATION_ERROR", "parentId is invalid"), status=400)
                cat.parent = parent
            else:
                cat.parent = None
        if "displayOrder" in body:
            cat.display_order = int(body["displayOrder"] or 0)
        if "isEngel" in body:
            cat.is_engel = bool(body["isEngel"])
        if "needsWants" in body:
            cat.needs_wants = str(body["needsWants"] or "needs")
        if "isHousing" in body:
            cat.is_housing = bool(body["isHousing"])
        if "isFixedExpense" in body:
            cat.is_fixed_expense = bool(body["isFixedExpense"])
        cat.save()
        return Response(_ok(_category_dict(cat)))

    def delete(self, request: Request, category_id: str) -> Response:
        try:
            cat = Category.objects.get(pk=category_id, user=request.user, is_deleted=False)
        except Category.DoesNotExist:
            return Response(_err("NOT_FOUND", "Category not found"), status=404)
        if Receipt.objects.filter(user=request.user, category=cat).exists():
            return Response(_err("CONFLICT", "Category has receipts; reassign before deletion"), status=409)
        cat.is_deleted = True
        cat.save(update_fields=["is_deleted"])
        return Response(_ok({"id": category_id, "deleted": True}))


# ── Shop ──────────────────────────────────────────────────────────────────────

def _shop_dict(shop: Shop) -> dict:
    return {
        "id": str(shop.id),
        "name": shop.name,
        "address": shop.address,
        "isActive": shop.is_active,
        "mergedIntoShopId": str(shop.merged_into_shop_id) if shop.merged_into_shop_id else None,
    }


class ShopListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        shops = Shop.objects.filter(user=request.user).order_by("name")
        return Response(_ok({"items": [_shop_dict(s) for s in shops]}))


class ShopMergeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, shop_id: str) -> Response:
        body = request.data or {}
        secondary_id = body.get("secondaryShopId", "")
        if not secondary_id:
            return Response(_err("VALIDATION_ERROR", "secondaryShopId is required"), status=400)
        if shop_id == secondary_id:
            return Response(_err("VALIDATION_ERROR", "primary and secondary shop must differ"), status=400)

        primary = Shop.objects.filter(pk=shop_id, user=request.user).first()
        secondary = Shop.objects.filter(pk=secondary_id, user=request.user).first()
        if not primary or not secondary:
            return Response(_err("NOT_FOUND", "Shop not found"), status=404)

        with transaction.atomic():
            Receipt.objects.filter(user=request.user, shop=secondary).update(shop=primary)
            CategoryMapping.objects.filter(user=request.user, shop=secondary).update(shop=primary)
            secondary.merged_into_shop = primary
            secondary.is_active = False
            secondary.save(update_fields=["merged_into_shop", "is_active"])

        return Response(_ok({"status": "merged"}))


# ── Payment Card ──────────────────────────────────────────────────────────────

def _card_dict(card: PaymentCard) -> dict:
    return {
        "id": str(card.id),
        "nickname": card.nickname,
        "cardType": card.card_type,
        "network": card.network,
        "colorHex": card.color_hex,
        "isActive": card.is_active,
    }


class CardListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        cards = PaymentCard.objects.filter(user=request.user).order_by("nickname")
        return Response(_ok({"items": [_card_dict(c) for c in cards]}))

    def post(self, request: Request) -> Response:
        body = request.data or {}
        nickname = (body.get("nickname") or "").strip()
        card_type = (body.get("cardType") or "").strip()
        if not nickname:
            return Response(_err("VALIDATION_ERROR", "nickname is required"), status=400)
        if not card_type:
            return Response(_err("VALIDATION_ERROR", "cardType is required"), status=400)
        card = PaymentCard.objects.create(
            user=request.user,
            nickname=nickname,
            card_type=card_type,
            network=(body.get("network") or "").strip() or None,
            color_hex=(body.get("colorHex") or "").strip() or None,
        )
        return Response(_ok(_card_dict(card)), status=201)


class CardDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, card_id: str) -> Response:
        try:
            card = PaymentCard.objects.get(pk=card_id, user=request.user)
        except PaymentCard.DoesNotExist:
            return Response(_err("NOT_FOUND", "Card not found"), status=404)
        card.is_active = False
        card.save(update_fields=["is_active"])
        return Response(_ok(_card_dict(card)))


# ── Category Mapping ──────────────────────────────────────────────────────────

class CategoryMappingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        mappings = (
            CategoryMapping.objects.filter(user=request.user)
            .select_related("shop", "category")
        )
        result = [
            {
                "id": str(m.id),
                "shopId": str(m.shop_id),
                "shopName": m.shop.name if m.shop else None,
                "categoryId": str(m.category_id),
                "categoryName": m.category.name if m.category else None,
                "confidence": m.confidence,
                "source": m.source,
            }
            for m in mappings
        ]
        return Response(_ok({"items": result}))


class CategoryMappingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, mapping_id: str) -> Response:
        category_id = (request.data or {}).get("categoryId", "")
        if not category_id:
            return Response(_err("VALIDATION_ERROR", "categoryId is required"), status=400)
        try:
            mapping = CategoryMapping.objects.get(pk=mapping_id, user=request.user)
        except CategoryMapping.DoesNotExist:
            return Response(_err("NOT_FOUND", "Mapping not found"), status=404)
        category = Category.objects.filter(pk=category_id, user=request.user, is_deleted=False).first()
        if not category:
            return Response(_err("NOT_FOUND", "Category not found"), status=404)
        mapping.category = category
        mapping.source = "user"
        mapping.save(update_fields=["category", "source"])
        return Response(_ok({
            "id": str(mapping.id),
            "shopId": str(mapping.shop_id),
            "categoryId": str(mapping.category_id),
            "confidence": mapping.confidence,
            "source": mapping.source,
        }))


# ── Budget ────────────────────────────────────────────────────────────────────

def _month_start(month: str) -> datetime:
    year, mon = month.split("-")
    return datetime(int(year), int(mon), 1, tzinfo=UTC)


def _next_month(month: str) -> str:
    year, mon = [int(v) for v in month.split("-")]
    mon += 1
    if mon == 13:
        year += 1
        mon = 1
    return f"{year:04d}-{mon:02d}"


def _prev_month(month: str) -> str:
    year, mon = [int(v) for v in month.split("-")]
    mon -= 1
    if mon == 0:
        year -= 1
        mon = 12
    return f"{year:04d}-{mon:02d}"


def _month_spend(user: Any, month: str, category_id: Any) -> float:
    start = _month_start(month)
    end = _month_start(_next_month(month))
    qs = Receipt.objects.filter(user=user, receipt_date__gte=start, receipt_date__lt=end)
    qs = qs.filter(category_id__isnull=True) if category_id is None else qs.filter(category_id=category_id)
    return float(qs.aggregate(total=Sum("total_amount"))["total"] or 0.0)


def _budget_dict(budget: Budget) -> dict:
    return {
        "id": str(budget.id),
        "month": budget.year_month,
        "categoryId": str(budget.category_id) if budget.category_id else None,
        "mode": budget.mode,
        "amount": round(float(budget.amount or 0.0), 2),
        "adjustmentPct": budget.adjustment_pct,
        "rolloverEnabled": bool(budget.rollover_enabled),
        "rolloverBalance": round(float(budget.rollover_balance or 0.0), 2),
    }


class BudgetListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        month = (request.query_params.get("month") or "").strip()
        if not month or not MONTH_RE.match(month):
            return Response(_err("VALIDATION_ERROR", "month query is required (YYYY-MM)"), status=400)
        budgets = Budget.objects.filter(user=request.user, year_month=month).order_by("category_id")
        return Response(_ok({"items": [_budget_dict(b) for b in budgets]}))

    def post(self, request: Request) -> Response:
        body = request.data or {}
        month = str(body.get("month") or body.get("yearMonth") or "").strip()
        if not month or not MONTH_RE.match(month):
            return Response(_err("VALIDATION_ERROR", "month must be YYYY-MM"), status=400)

        category_id = body.get("categoryId") or None
        mode = str(body.get("mode") or "manual").strip()
        valid_modes = {"manual", "forecast", "forecast_adjusted"}
        if mode not in valid_modes:
            return Response(_err("VALIDATION_ERROR", f"mode must be one of {', '.join(valid_modes)}"), status=400)

        try:
            amount = float(body.get("amount") or 0)
        except (TypeError, ValueError):
            return Response(_err("VALIDATION_ERROR", "amount must be a number"), status=400)
        if amount < 0:
            return Response(_err("VALIDATION_ERROR", "amount must be non-negative"), status=400)

        adjustment_pct = body.get("adjustmentPct")
        if adjustment_pct is not None:
            try:
                adjustment_pct = int(adjustment_pct)
            except (TypeError, ValueError):
                return Response(_err("VALIDATION_ERROR", "adjustmentPct must be an integer"), status=400)
            if not 80 <= adjustment_pct <= 120:
                return Response(_err("VALIDATION_ERROR", "adjustmentPct must be 80–120"), status=400)

        if mode == "forecast_adjusted" and adjustment_pct is None:
            return Response(_err("VALIDATION_ERROR", "adjustmentPct is required for forecast_adjusted"), status=400)

        if mode in {"forecast", "forecast_adjusted"}:
            start = _month_start(month)
            window_start = _month_start(_prev_month(_prev_month(_prev_month(month))))
            qs = Receipt.objects.filter(
                user=request.user, receipt_date__gte=window_start, receipt_date__lt=start
            )
            qs = qs.filter(category_id__isnull=True) if category_id is None else qs.filter(category_id=category_id)
            base = float(qs.aggregate(total=Sum("total_amount"))["total"] or 0.0) / 3.0 or amount
            amount = round(base * (adjustment_pct / 100.0), 2) if mode == "forecast_adjusted" else round(base, 2)

        rollover_enabled = bool(body.get("rolloverEnabled", False))
        rollover_balance = 0.0
        if rollover_enabled:
            prev = _prev_month(month)
            prev_budget_qs = Budget.objects.filter(user=request.user, year_month=prev)
            prev_budget_qs = (
                prev_budget_qs.filter(category_id__isnull=True)
                if category_id is None
                else prev_budget_qs.filter(category_id=category_id)
            )
            prev_budget = prev_budget_qs.first()
            if prev_budget and prev_budget.rollover_enabled:
                available = float(prev_budget.amount or 0) + float(prev_budget.rollover_balance or 0)
                rollover_balance = round(available - _month_spend(request.user, prev, category_id), 2)

        qs = Budget.objects.filter(user=request.user, year_month=month)
        qs = qs.filter(category_id__isnull=True) if category_id is None else qs.filter(category_id=category_id)
        budget = qs.first()
        if not budget:
            budget = Budget(user=request.user, year_month=month, category_id=category_id)
        budget.mode = mode
        budget.amount = amount
        budget.adjustment_pct = adjustment_pct
        budget.rollover_enabled = rollover_enabled
        budget.rollover_balance = rollover_balance
        budget.save()
        return Response(_ok(_budget_dict(budget)))


class BudgetProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        month = (request.query_params.get("month") or "").strip()
        if not month or not MONTH_RE.match(month):
            return Response(_err("VALIDATION_ERROR", "month query is required (YYYY-MM)"), status=400)

        budgets = Budget.objects.filter(user=request.user, year_month=month).order_by("category_id")
        result = []
        for b in budgets:
            spent = _month_spend(request.user, month, b.category_id)
            budget_amount = float(b.amount or 0)
            rollover = float(b.rollover_balance or 0)
            available = budget_amount + rollover - spent
            result.append({
                **_budget_dict(b),
                "spent": round(spent, 2),
                "remaining": round(available, 2),
                "percentUsed": round(spent / budget_amount * 100, 1) if budget_amount > 0 else 0.0,
            })
        return Response(_ok({"items": result}))


# ── Pairing ───────────────────────────────────────────────────────────────────

class PairingQRView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        token = secrets.token_urlsafe(24)
        expires_at = datetime.now(tz=UTC) + timedelta(seconds=settings.QR_PAIRING_TOKEN_TTL_SECONDS)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        PairingToken.objects.create(user=user, token_hash=token_hash, expires_at=expires_at)
        return Response(_ok({
            "qrPayload": {
                "serverBaseUrl": settings.API_BASE_URL,
                "pairingToken": token,
                "expiresAt": expires_at.isoformat(),
            }
        }))


class PairingValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        token = (request.data or {}).get("pairingToken", "")
        if not token:
            return Response(_err("VALIDATION_ERROR", "pairingToken is required"), status=400)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        pairing = PairingToken.objects.filter(
            user=request.user, token_hash=token_hash, consumed_at__isnull=True
        ).first()
        if not pairing or pairing.expires_at < datetime.now(tz=UTC):
            return Response(_err("INVALID_TOKEN", "Pairing token invalid or expired"), status=401)
        pairing.consumed_at = datetime.now(tz=UTC)
        pairing.save(update_fields=["consumed_at"])
        return Response(_ok({"valid": True}))


# ── Analytics ─────────────────────────────────────────────────────────────────

def _period_bounds(period: str) -> tuple[datetime, datetime]:
    now = datetime.now(tz=UTC)
    if period == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "last_month":
        first_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = first_this
        prev_month_end = first_this - timedelta(days=1)
        start = prev_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "last_3_months":
        end = now
        start = (now - timedelta(days=92)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "this_year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    return start, end


def _receipt_qs_for_period(user: Any, currency: str, start: datetime, end: datetime):
    qs = Receipt.objects.filter(user=user, receipt_date__gte=start, receipt_date__lt=end)
    if currency and currency != "ALL":
        qs = qs.filter(currency=currency)
    return qs


class AnalyticsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        period = request.query_params.get("period", "this_month")
        currency = request.query_params.get("currency", "USD")
        start, end = _period_bounds(period)
        qs = _receipt_qs_for_period(request.user, currency, start, end)

        total = float(qs.aggregate(total=Sum("total_amount"))["total"] or 0.0)
        count = qs.count()

        top_categories = list(
            qs.values("category_id", "category__name")
            .annotate(amount=Sum("total_amount"))
            .order_by("-amount")[:5]
        )
        top_shops = list(
            qs.values("shop_id", "shop__name")
            .annotate(amount=Sum("total_amount"))
            .order_by("-amount")[:5]
        )

        return Response(_ok({
            "period": period,
            "currency": currency,
            "totalSpending": round(total, 2),
            "receiptCount": count,
            "topCategories": [
                {
                    "categoryId": str(r["category_id"]) if r["category_id"] else None,
                    "name": r["category__name"] or "Uncategorized",
                    "amount": round(float(r["amount"] or 0), 2),
                }
                for r in top_categories
            ],
            "topShops": [
                {
                    "shopId": str(r["shop_id"]) if r["shop_id"] else None,
                    "name": r["shop__name"] or "Unknown Shop",
                    "amount": round(float(r["amount"] or 0), 2),
                }
                for r in top_shops
            ],
        }))


class AnalyticsCategoryBreakdownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        period = request.query_params.get("period", "this_month")
        currency = request.query_params.get("currency", "USD")
        start, end = _period_bounds(period)
        qs = _receipt_qs_for_period(request.user, currency, start, end)

        rows = list(
            qs.values("category_id", "category__name")
            .annotate(amount=Sum("total_amount"))
            .order_by("-amount")
        )
        items = [
            {
                "categoryId": str(r["category_id"]) if r["category_id"] else None,
                "name": r["category__name"] or "Uncategorized",
                "amount": round(float(r["amount"] or 0), 2),
            }
            for r in rows
        ]
        return Response(_ok({"items": items}))


class AnalyticsCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        period = request.query_params.get("period", "this_month")
        currency = request.query_params.get("currency", "USD")
        start, end = _period_bounds(period)
        qs = _receipt_qs_for_period(request.user, currency, start, end)

        from django.db.models.functions import TruncDate
        rows = list(
            qs.annotate(day=TruncDate("receipt_date"))
            .values("day")
            .annotate(amount=Sum("total_amount"))
            .order_by("day")
        )
        days = [
            {"date": r["day"].isoformat(), "amount": round(float(r["amount"] or 0), 2)}
            for r in rows
        ]
        return Response(_ok({"days": days}))


class AnalyticsYoYView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        currency = request.query_params.get("currency", "USD")
        now = datetime.now(tz=UTC)
        items = []
        for month_offset in range(11, -1, -1):
            total_months = now.month - 1 - month_offset
            year = now.year + (total_months // 12)
            month = (total_months % 12) + 1
            if month <= 0:
                month += 12
                year -= 1
            start = datetime(year, month, 1, tzinfo=UTC)
            end_month = month + 1 if month < 12 else 1
            end_year = year if month < 12 else year + 1
            end = datetime(end_year, end_month, 1, tzinfo=UTC)
            total = float(
                _receipt_qs_for_period(request.user, currency, start, end)
                .aggregate(t=Sum("total_amount"))["t"] or 0
            )
            items.append({"month": f"{year:04d}-{month:02d}", "amount": round(total, 2)})
        return Response(_ok({"items": items}))


class AnalyticsBLSView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(_ok({"benchmarks": [], "message": "BLS benchmark data not yet available"}))


class AnalyticsInsightsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        period = request.query_params.get("period", "this_month")
        currency = request.query_params.get("currency", "USD")
        start, end = _period_bounds(period)
        qs = _receipt_qs_for_period(request.user, currency, start, end)
        total = float(qs.aggregate(t=Sum("total_amount"))["t"] or 0)
        count = qs.count()
        avg = round(total / count, 2) if count > 0 else 0.0
        return Response(_ok({
            "period": period,
            "currency": currency,
            "totalSpending": round(total, 2),
            "receiptCount": count,
            "averageReceiptAmount": avg,
        }))


# ── Recurring ─────────────────────────────────────────────────────────────────

class RecurringListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        templates = list(RecurringExpenseTemplate.objects.filter(user=request.user).order_by("name"))
        upcoming = list(
            RecurringExpenseOccurrence.objects.filter(
                template__user=request.user, status="upcoming"
            ).select_related("template").order_by("due_date")[:20]
        )
        return Response(_ok({
            "templates": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "expectedAmount": t.expected_amount,
                    "frequency": t.frequency,
                    "startDate": t.start_date.isoformat(),
                }
                for t in templates
            ],
            "upcoming": [
                {
                    "id": str(o.id),
                    "templateId": str(o.template_id),
                    "templateName": o.template.name,
                    "dueDate": o.due_date.isoformat(),
                    "status": o.status,
                }
                for o in upcoming
            ],
        }))

    def post(self, request: Request) -> Response:
        body = request.data or {}
        name = (body.get("name") or "").strip()
        if not name:
            return Response(_err("VALIDATION_ERROR", "name is required"), status=400)
        template = RecurringExpenseTemplate.objects.create(
            user=request.user,
            name=name,
            expected_amount=float(body.get("expectedAmount") or 0),
            frequency=str(body.get("frequency") or "monthly"),
            start_date=_parse_dt(body.get("startDate")),
        )
        return Response(_ok({
            "id": str(template.id),
            "name": template.name,
            "expectedAmount": template.expected_amount,
            "frequency": template.frequency,
            "startDate": template.start_date.isoformat(),
        }), status=201)


# ── Export ────────────────────────────────────────────────────────────────────

class ExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        export_format = request.query_params.get("format", "json")
        count = Receipt.objects.filter(user=request.user).count()
        return Response(_ok({
            "format": export_format,
            "receiptCount": count,
            "message": "Export feature coming soon. Use the sync endpoint to retrieve data.",
        }))


# ── Amortization ──────────────────────────────────────────────────────────────

def _amortization_dict(rule: AmortizationRule) -> dict:
    return {
        "id": str(rule.id),
        "title": rule.title,
        "totalAmount": rule.total_amount,
        "months": rule.months,
        "monthlyAmount": rule.monthly_amount,
        "status": rule.status,
    }


class AmortizationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        rules = AmortizationRule.objects.filter(user=request.user).order_by("title")
        return Response(_ok({"items": [_amortization_dict(r) for r in rules]}))

    def post(self, request: Request) -> Response:
        body = request.data or {}
        title = (body.get("title") or "").strip()
        if not title:
            return Response(_err("VALIDATION_ERROR", "title is required"), status=400)
        try:
            total_amount = float(body.get("totalAmount") or 0)
            months = int(body.get("months") or 12)
        except (TypeError, ValueError):
            return Response(_err("VALIDATION_ERROR", "totalAmount and months must be numbers"), status=400)
        monthly_amount = round(total_amount / months, 2) if months > 0 else 0.0
        rule = AmortizationRule.objects.create(
            user=request.user,
            title=title,
            total_amount=total_amount,
            months=months,
            monthly_amount=float(body.get("monthlyAmount") or monthly_amount),
            status="active",
        )
        return Response(_ok(_amortization_dict(rule)), status=201)


class AmortizationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, rule_id: str) -> Response:
        try:
            rule = AmortizationRule.objects.get(pk=rule_id, user=request.user)
        except AmortizationRule.DoesNotExist:
            return Response(_err("NOT_FOUND", "Rule not found"), status=404)
        rule.delete()
        return Response(_ok({"id": rule_id, "deleted": True}))
