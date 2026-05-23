import logging

from flask import Blueprint, jsonify, request

from api.envelope import ok
from config.database import SessionLocal
from services.amazon_import_service import AmazonImportService
from services.receipt_bulk_service import ReceiptBulkService
from services.receipt_service import ReceiptService
from utils.auth import get_current_user_id


bp = Blueprint("receipts", __name__)
logger = logging.getLogger(__name__)


@bp.get("")
def list_receipts() -> tuple:
    user_id = get_current_user_id()
    filters = dict(request.args)
    db = SessionLocal()
    try:
        receipt_service = ReceiptService(db)
        items = receipt_service.list_receipts(user_id, filters)
        logger.info(
            "receipts list user_id=%s filters=%s returned=%s",
            user_id,
            filters,
            len(items),
        )
        data = {"items": items}
        return jsonify(ok(data)), 200
    finally:
        db.close()


@bp.get("/<receipt_id>")
def get_receipt(receipt_id: str) -> tuple:
    user_id = get_current_user_id()
    db = SessionLocal()
    try:
        receipt_service = ReceiptService(db)
        data = receipt_service.get_receipt(user_id, receipt_id)
        return jsonify(ok(data)), 200
    finally:
        db.close()


@bp.patch("/<receipt_id>")
def update_receipt(receipt_id: str) -> tuple:
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        receipt_service = ReceiptService(db)
        data = receipt_service.update_receipt(user_id, receipt_id, body)
        return jsonify(ok(data)), 200
    finally:
        db.close()


@bp.post("/bulk")
def bulk_receipts() -> tuple:
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    op = body.get("operation", "")
    ids = body.get("receiptIds", [])
    db = SessionLocal()
    try:
        bulk_service = ReceiptBulkService(db)
        data = bulk_service.apply(op, ids, {**body, "userId": user_id})
        return jsonify(ok(data)), 200
    finally:
        db.close()


@bp.post("/import/amazon")
def import_amazon() -> tuple:
    user_id = get_current_user_id()
    upload = request.files.get("file")
    payload = upload.read() if upload else b""
    db = SessionLocal()
    try:
        amazon_service = AmazonImportService(db)
        data = amazon_service.import_rows(user_id, payload)
        return jsonify(ok(data)), 200
    finally:
        db.close()
