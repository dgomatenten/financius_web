"""Android device QR pairing API endpoints"""

from flask import Blueprint, jsonify, request

from api.envelope import ok
from config.database import SessionLocal
from services.pairing_service import PairingService
from utils.auth import get_current_user_id
from utils.exceptions import ValidationError


bp = Blueprint("pairing", __name__)


@bp.get("/qr")
def pairing_qr() -> tuple:
    """
    Generate a new QR code pairing token for the current user.
    The token is embedded in a QR code that the Android app scans.
    
    Response: {
        "data": {
            "serverBaseUrl": "http://localhost:8000",
            "pairingToken": "...",
            "expiresAt": "2026-05-17T..."
        },
        "error": null
    }
    """
    user_id = get_current_user_id()
    
    db = SessionLocal()
    try:
        service = PairingService(db)
        qr_payload = service.generate_pairing_token(user_id)
        return jsonify(ok({"qrPayload": qr_payload})), 200
    finally:
        db.close()


@bp.post("/validate")
def validate_pairing() -> tuple:
    """Validate a pairing token for the current authenticated user."""
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    token = body.get("pairingToken")
    if not token:
        raise ValidationError("pairingToken is required")

    db = SessionLocal()
    try:
        service = PairingService(db)
        service.validate_pairing_token(user_id, token)
        return jsonify(ok({"valid": True})), 200
    finally:
        db.close()
