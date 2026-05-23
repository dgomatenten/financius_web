from typing import Any

from repositories.receipt_repository import ReceiptRepository
from utils.exceptions import ValidationError


class ReceiptBulkService:
    def __init__(self, db_session=None):
        self.repository = ReceiptRepository(db_session)

    def apply(self, operation: str, receipt_ids: list[str], payload: dict[str, Any]) -> dict[str, int]:
        if operation not in {"recategorize", "reassign_card", "delete"}:
            raise ValidationError("Invalid bulk operation")
        if not receipt_ids:
            raise ValidationError("receiptIds is required")

        if operation == "recategorize" and not payload.get("categoryId"):
            raise ValidationError("categoryId is required for recategorize")
        if operation == "reassign_card" and not payload.get("paymentCardId"):
            raise ValidationError("paymentCardId is required for reassign_card")

        user_id = payload.get("userId")
        if not user_id:
            raise ValidationError("userId is required")

        affected = self.repository.bulk_apply(user_id, operation, receipt_ids, payload)
        return {"affectedCount": affected}
