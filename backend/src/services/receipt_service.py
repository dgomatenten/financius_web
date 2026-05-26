from typing import Any

from repositories.receipt_repository import ReceiptRepository
from utils.exceptions import UserNotFoundError, ValidationError


class ReceiptService:
    def __init__(self, db_session=None) -> None:
        self.repository = ReceiptRepository(db_session)

    def list_receipts(self, user_id: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        if not user_id:
            raise ValidationError("userId is required")
        return self.repository.list_receipts(user_id, filters)

    def get_receipt(self, user_id: str, receipt_id: str) -> dict[str, Any]:
        if not receipt_id:
            raise ValidationError("receiptId is required")
        receipt = self.repository.get_receipt(user_id, receipt_id)
        if not receipt:
            raise UserNotFoundError()
        return receipt

    def update_receipt(self, user_id: str, receipt_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        allowed = {"categoryId", "paymentCardId", "note"}
        unknown_fields = [key for key in payload.keys() if key not in allowed]
        if unknown_fields:
            raise ValidationError("Unsupported receipt update fields")
        receipt = self.repository.update_receipt(user_id, receipt_id, payload)
        if not receipt:
            raise UserNotFoundError()
        return receipt
