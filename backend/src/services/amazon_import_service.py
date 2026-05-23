from typing import Any
import csv
import io
from datetime import datetime

from repositories.receipt_repository import ReceiptRepository
from utils.exceptions import ValidationError


class AmazonImportService:
    def __init__(self, db_session=None):
        self.repository = ReceiptRepository(db_session)

    def import_rows(self, user_id: str, raw_csv: bytes) -> dict[str, Any]:
        if not raw_csv:
            raise ValidationError("CSV file is required")

        content = raw_csv.decode("utf-8-sig", errors="ignore")
        reader = csv.DictReader(io.StringIO(content))
        affected = 0
        for row in reader:
            receipt_date = self._parse_date(row.get("receiptDate") or row.get("date"))
            currency = (row.get("currency") or "USD").strip() or "USD"
            total_amount = self._to_float(row.get("totalAmount") or row.get("total") or 0)
            shop_name = (row.get("shopName") or row.get("shop") or "").strip() or None
            item_name = (row.get("itemName") or row.get("description") or "Amazon Item").strip()
            quantity = self._to_float(row.get("quantity") or 1)
            unit_price = self._to_float(row.get("unitPrice") or total_amount)

            self.repository.create_receipt_with_lines(
                user_id=user_id,
                receipt_date=receipt_date,
                currency=currency,
                total_amount=total_amount,
                shop_name=shop_name,
                line_items=[
                    {
                        "name": item_name,
                        "quantity": quantity,
                        "unitPrice": unit_price,
                        "lineTotal": quantity * unit_price,
                    }
                ],
                note="Imported from Amazon CSV",
            )
            affected += 1

        return {"affectedCount": affected}

    def _to_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _parse_date(self, value: str | None) -> datetime:
        if not value:
            return datetime.utcnow()
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.utcnow()
