"""Repository for synced data operations"""

from typing import Any
from uuid import uuid4
from datetime import datetime, timezone

from config.database import SessionLocal
from models.receipt import Receipt, ReceiptLineItem
from models.category import Category
from models.master_data import Shop, PaymentCard


class SyncRepository:
    """Database access layer for synced data"""

    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal

    def upsert_payload(self, user_id: str, payload: dict[str, Any]) -> dict[str, int]:
        """
        Idempotently upsert synced data (receipts, categories, shops, cards).
        
        Idempotent means: sending same data twice = no duplicates.
        Uses external_id to detect existing records.
        """
        # Upsert master data first so receipts can reference them in the same payload.
        categories_result = self._upsert_categories(user_id, payload.get("categories", []))
        shops_result = self._upsert_shops(user_id, payload.get("shops", []))
        cards_result = self._upsert_cards(user_id, payload.get("cards", []))
        receipts_result = self._upsert_receipts(user_id, payload.get("receipts", []))

        return {
            "receipts": receipts_result["accepted"],
            "receiptsNew": receipts_result["new"],
            "receiptsDuplicates": receipts_result["duplicates"],
            "categories": categories_result["accepted"],
            "categoriesNew": categories_result["new"],
            "categoriesDuplicates": categories_result["duplicates"],
            "shops": shops_result["accepted"],
            "shopsNew": shops_result["new"],
            "shopsDuplicates": shops_result["duplicates"],
            "cards": cards_result["accepted"],
            "cardsNew": cards_result["new"],
            "cardsDuplicates": cards_result["duplicates"],
            "lineItems": receipts_result["lineItems"],
            "duplicates": (
                receipts_result["duplicates"]
                + categories_result["duplicates"]
                + shops_result["duplicates"]
                + cards_result["duplicates"]
            ),
        }

    def _parse_iso_datetime(self, iso_string: str | None) -> datetime:
        """Parse ISO 8601 datetime string, return aware datetime in UTC"""
        if not iso_string:
            return datetime.now(tz=timezone.utc)
        try:
            # Replace 'Z' suffix with '+00:00' for fromisoformat compatibility
            iso_string = iso_string.replace('Z', '+00:00')
            dt = datetime.fromisoformat(iso_string)
            # Ensure it's timezone-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return datetime.now(tz=timezone.utc)

    def _upsert_receipts(self, user_id: str, receipts_list: list[dict]) -> dict[str, int]:
        """
        Upsert receipts by (user_id, external_id).
        If exists: update. If new: create.
        """
        accepted = 0
        duplicates = 0
        line_items_count = 0
        for receipt_data in receipts_list:
            if not isinstance(receipt_data, dict):
                continue
            external_id = receipt_data.get("externalId")
            if not external_id:
                continue

            # Find existing receipt
            existing = (
                self.db.query(Receipt)
                .filter(Receipt.user_id == user_id, Receipt.external_id == external_id)
                .first()
            )

            shop_id = self._resolve_shop_id(user_id, receipt_data)
            category_id = self._resolve_category_id(user_id, receipt_data)
            payment_card_id = self._resolve_card_id(user_id, receipt_data)

            if existing:
                # Update existing receipt
                existing.receipt_date = self._parse_iso_datetime(receipt_data.get("receiptDate") or receipt_data.get("date"))
                existing.currency = receipt_data.get("currency", existing.currency)
                existing.total_amount = receipt_data.get("total", receipt_data.get("totalAmount", existing.total_amount))
                if shop_id:
                    existing.shop_id = shop_id
                if category_id:
                    existing.category_id = category_id
                if payment_card_id:
                    existing.payment_card_id = payment_card_id
                duplicates += 1
            else:
                # Create new receipt
                receipt = Receipt(
                    id=str(uuid4()),
                    user_id=user_id,
                    external_id=external_id,
                    shop_id=shop_id,
                    category_id=category_id,
                    payment_card_id=payment_card_id,
                    receipt_date=self._parse_iso_datetime(receipt_data.get("receiptDate") or receipt_data.get("date")),
                    currency=receipt_data.get("currency", "USD"),
                    total_amount=receipt_data.get("total", receipt_data.get("totalAmount", 0)),
                )
                self.db.add(receipt)
                self.db.flush()

                # Add line items
                for line_item_data in receipt_data.get("lineItems", []):
                    if not isinstance(line_item_data, dict):
                        continue
                    quantity = line_item_data.get("quantity", 1)
                    unit_price = line_item_data.get("unitPrice", 0)
                    line_item = ReceiptLineItem(
                        id=str(uuid4()),
                        receipt_id=receipt.id,
                        name=line_item_data.get("name", ""),
                        quantity=quantity,
                        unit_price=unit_price,
                    )
                    self.db.add(line_item)
                    line_items_count += 1

            accepted += 1

        self.db.commit()

        return {
            "accepted": accepted,
            "new": max(accepted - duplicates, 0),
            "duplicates": duplicates,
            "lineItems": line_items_count,
        }

    def _upsert_categories(self, user_id: str, categories_list: list[dict]) -> dict[str, int]:
        """Upsert categories by (user_id, external_id)"""
        accepted = 0
        duplicates = 0
        for cat_data in categories_list:
            if not isinstance(cat_data, dict):
                continue
            external_id = cat_data.get("externalId")
            if not external_id:
                continue

            existing = (
                self.db.query(Category.id, Category.name)
                .filter(Category.user_id == user_id, Category.external_id == external_id)
                .first()
            )

            if existing:
                self.db.query(Category).filter(Category.id == existing.id).update(
                    {"name": cat_data.get("name", existing.name)}
                )
                duplicates += 1
            else:
                category = Category(
                    id=str(uuid4()),
                    user_id=user_id,
                    external_id=external_id,
                    name=cat_data.get("name", ""),
                )
                self.db.add(category)
            accepted += 1

        self.db.commit()

        return {"accepted": accepted, "new": max(accepted - duplicates, 0), "duplicates": duplicates}

    def _resolve_shop_id(self, user_id: str, receipt_data: dict[str, Any]) -> str | None:
        shop_db_id = receipt_data.get("shopDbId") or receipt_data.get("shop_id")
        if shop_db_id:
            return str(shop_db_id)

        shop_external_id = receipt_data.get("shopExternalId") or receipt_data.get("shopId")
        if shop_external_id:
            shop = (
                self.db.query(Shop)
                .filter(Shop.user_id == user_id, Shop.external_id == str(shop_external_id))
                .first()
            )
            if shop:
                return shop.id

        shop_name = receipt_data.get("shopName") or receipt_data.get("merchant")
        if shop_name:
            shop = (
                self.db.query(Shop)
                .filter(Shop.user_id == user_id, Shop.name == str(shop_name))
                .first()
            )
            if shop:
                return shop.id

        return None

    def _resolve_category_id(self, user_id: str, receipt_data: dict[str, Any]) -> str | None:
        category_db_id = receipt_data.get("categoryDbId") or receipt_data.get("category_id")
        if category_db_id:
            return str(category_db_id)

        category_external_id = receipt_data.get("categoryExternalId") or receipt_data.get("categoryId")
        if category_external_id:
            category = (
                self.db.query(Category.id)
                .filter(Category.user_id == user_id, Category.external_id == str(category_external_id))
                .first()
            )
            if category:
                return category.id

        return None

    def _resolve_card_id(self, user_id: str, receipt_data: dict[str, Any]) -> str | None:
        card_db_id = receipt_data.get("paymentCardDbId") or receipt_data.get("payment_card_id")
        if card_db_id:
            return str(card_db_id)

        card_external_id = (
            receipt_data.get("paymentCardExternalId")
            or receipt_data.get("paymentCardId")
            or receipt_data.get("cardExternalId")
            or receipt_data.get("cardId")
        )
        if card_external_id:
            card = (
                self.db.query(PaymentCard)
                .filter(PaymentCard.user_id == user_id, PaymentCard.external_id == str(card_external_id))
                .first()
            )
            if card:
                return card.id

        return None

    def _upsert_shops(self, user_id: str, shops_list: list[dict]) -> dict[str, int]:
        """Upsert shops by (user_id, external_id)"""
        accepted = 0
        duplicates = 0
        for shop_data in shops_list:
            if not isinstance(shop_data, dict):
                continue
            external_id = shop_data.get("externalId")
            if not external_id:
                continue

            existing = (
                self.db.query(Shop)
                .filter(Shop.user_id == user_id, Shop.external_id == external_id)
                .first()
            )

            if existing:
                existing.name = shop_data.get("name", existing.name)
                existing.address = shop_data.get("address", existing.address)
                duplicates += 1
            else:
                shop = Shop(
                    id=str(uuid4()),
                    user_id=user_id,
                    external_id=external_id,
                    name=shop_data.get("name", ""),
                    address=shop_data.get("address"),
                )
                self.db.add(shop)
            accepted += 1

        self.db.commit()

        return {"accepted": accepted, "new": max(accepted - duplicates, 0), "duplicates": duplicates}

    def _upsert_cards(self, user_id: str, cards_list: list[dict]) -> dict[str, int]:
        """Upsert payment cards by (user_id, external_id)"""
        accepted = 0
        duplicates = 0
        for card_data in cards_list:
            if not isinstance(card_data, dict):
                continue
            external_id = card_data.get("externalId")
            if not external_id:
                continue

            existing = (
                self.db.query(PaymentCard)
                .filter(PaymentCard.user_id == user_id, PaymentCard.external_id == external_id)
                .first()
            )

            if existing:
                existing.nickname = card_data.get("nickname", existing.nickname)
                existing.card_type = card_data.get("cardType", existing.card_type)
                duplicates += 1
            else:
                card = PaymentCard(
                    id=str(uuid4()),
                    user_id=user_id,
                    external_id=external_id,
                    nickname=card_data.get("nickname", ""),
                    card_type=card_data.get("cardType", "credit"),
                )
                self.db.add(card)
            accepted += 1

        self.db.commit()

        return {"accepted": accepted, "new": max(accepted - duplicates, 0), "duplicates": duplicates}
