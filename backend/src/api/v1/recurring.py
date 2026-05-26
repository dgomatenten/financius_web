from flask import Blueprint, jsonify, request

from api.envelope import ok
from services.recurring_service import RecurringService

bp = Blueprint("recurring", __name__)
service = RecurringService()


@bp.get("/recurring")
def list_recurring() -> tuple:
    return jsonify(ok(service.list_all("demo-user"))), 200


@bp.post("/recurring")
def create_recurring() -> tuple:
    body = request.get_json(silent=True) or {}
    return jsonify(ok(body)), 201
