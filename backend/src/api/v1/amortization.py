from flask import Blueprint, jsonify, request

from api.envelope import ok
from services.amortization_service import AmortizationService

bp = Blueprint("amortization", __name__)
service = AmortizationService()


@bp.get("/amortization")
def list_amortization() -> tuple:
    return jsonify(ok(service.list_all("demo-user"))), 200


@bp.post("/amortization")
def create_amortization() -> tuple:
    body = request.get_json(silent=True) or {}
    return jsonify(ok(body)), 201


@bp.delete("/amortization/<rule_id>")
def delete_amortization(rule_id: str) -> tuple:
    return jsonify(ok({"id": rule_id, "deleted": True})), 200
