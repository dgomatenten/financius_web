from datetime import datetime
from typing import Any
from uuid import uuid4

from config.database import SessionLocal
from models.master_data import Shop
from models.receipt import Receipt, ReceiptLineItem


class ReceiptRepository:
    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal

    def list_receipts(self, user_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        query = self.db.query(Receipt).filter(Receipt.user_id == user_id)

        currency = filters.get("currency")
        if currency:
            query = query.filter(Receipt.currency == currency)

        category_id = filters.get("categoryId")
        if category_id:
            query = query.filter(Receipt.category_id == category_id)

        from_date = filters.get("fromDate")
        if from_date:
            query = query.filter(Receipt.receipt_date >= self._parse_iso_datetime(from_date))

        to_date = filters.get("toDate")
        if to_date:
            query = query.filter(Receipt.receipt_date <= self._parse_iso_datetime(to_date))

        search = filters.get("search")
        if search:
            query = query.filter(Receipt.note.ilike(f"%{search}%"))

        page = max(int(filters.get("page", 1)), 1)
        page_size = max(min(int(filters.get("pageSize", 20)), 100), 1)
        offset = (page - 1) * page_size

        receipts = (
            query.order_by(Receipt.receipt_date.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._to_receipt_summary(item) for item in receipts]

    def get_receipt(self, user_id: str, receipt_id: str) -> dict[str, Any] | None:
        receipt = (
            self.db.query(Receipt)
            .filter(Receipt.user_id == user_id, Receipt.id == receipt_id)
            .first()
        )
        if not receipt:
            return None

        line_items = (
            self.db.query(ReceiptLineItem)
            .filter(ReceiptLineItem.receipt_id == receipt.id)
            .all()
        )
        data = self._to_receipt_summary(receipt)
        data["lineItems"] = [
            {
                "name": item.name,
                "quantity": item.quantity,
                "unitPrice": item.unit_price,
                "lineTotal": item.line_total,
            }
            for item in line_items
        ]
        return data

    def update_receipt(self, user_id: str, receipt_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        receipt = (
            self.db.query(Receipt)
            .filter(Receipt.user_id == user_id, Receipt.id == receipt_id)
            .first()
        )
        if not receipt:
            return None

        if "categoryId" in payload:
            receipt.category_id = payload.get("categoryId")
        if "paymentCardId" in payload:
            receipt.payment_card_id = payload.get("paymentCardId")
        if "note" in payload:
            receipt.note = payload.get("note")

        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return self.get_receipt(user_id, receipt_id)

    def bulk_apply(self, user_id: str, operation: str, receipt_ids: list[str], payload: dict[str, Any]) -> int:
        query = self.db.query(Receipt).filter(Receipt.user_id == user_id, Receipt.id.in_(receipt_ids))
        receipts = query.all()
        if not receipts:
            return 0

        if operation == "recategorize":
            category_id = payload.get("categoryId")
            for receipt in receipts:
                receipt.category_id = category_id
                self.db.add(receipt)
        elif operation == "reassign_card":
            payment_card_id = payload.get("paymentCardId")
            for receipt in receipts:
                receipt.payment_card_id = payment_card_id
                self.db.add(receipt)
        elif operation == "delete":
            for receipt in receipts:
                self.db.query(ReceiptLineItem).filter(ReceiptLineItem.receipt_id == receipt.id).delete()
                self.db.delete(receipt)
        else:
            return 0

        self.db.commit()
        return len(receipts)

    def create_receipt_with_lines(
        self,
        user_id: str,
        receipt_date: datetime,
        currency: str,
        total_amount: float,
        shop_name: str | None,
        line_items: list[dict[str, Any]],
        note: str | None = None,
    ) -> str:
        shop_id = None
        if shop_name:
            existing_shop = (
                self.db.query(Shop)
                .filter(Shop.user_id == user_id, Shop.name == shop_name)
                .first()
            )
            if existing_shop:
                shop_id = existing_shop.id

        receipt = Receipt(
            id=str(uuid4()),
            user_id=user_id,
            external_id=f"import-{uuid4()}",
            shop_id=shop_id,
            receipt_date=receipt_date,
            currency=currency,
            total_amount=total_amount,
            note=note,
        )
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)

        for line in line_items:
            quantity = float(line.get("quantity", 1) or 1)
            unit_price = float(line.get("unitPrice", 0) or 0)
            line_total = float(line.get("lineTotal", quantity * unit_price))
            line_item = ReceiptLineItem(
                id=str(uuid4()),
                receipt_id=receipt.id,
                name=str(line.get("name", "")),
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
            self.db.add(line_item)

        self.db.commit()
        return receipt.id

    def _to_receipt_summary(self, receipt: Receipt) -> dict[str, Any]:
        shop_name = None
        if receipt.shop_id:
            shop = self.db.query(Shop).filter(Shop.id == receipt.shop_id).first()
            shop_name = shop.name if shop else None
        return {
            "id": receipt.id,
            "receiptDate": receipt.receipt_date.isoformat(),
            "shopName": shop_name,
            "totalAmount": receipt.total_amount,
            "currency": receipt.currency,
            "categoryId": receipt.category_id,
            "note": receipt.note,
            "paymentCardId": receipt.payment_card_id,
        }

    def _parse_iso_datetime(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
