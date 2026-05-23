from flask import Blueprint, jsonify, request

from api.envelope import ok
from config.database import SessionLocal
from services.budget_progress_service import BudgetProgressService
from services.budget_service import BudgetService
from utils.auth import get_current_user_id
from utils.exceptions import ValidationError


bp = Blueprint("budgets", __name__)


@bp.get("")
def list_budgets() -> tuple:
    user_id = get_current_user_id()
    month = (request.args.get("month") or "").strip()
    if not month:
        raise ValidationError("month query is required")

    db = SessionLocal()
    try:
        budget_service = BudgetService(db)
        return jsonify(ok(budget_service.list_for_month(user_id, month))), 200
    finally:
        db.close()


@bp.get("/progress")
def budget_progress() -> tuple:
    user_id = get_current_user_id()
    month = (request.args.get("month") or "").strip()
    if not month:
        raise ValidationError("month query is required")

    db = SessionLocal()
    try:
        progress_service = BudgetProgressService(db)
        return jsonify(ok(progress_service.progress(user_id, month))), 200
    finally:
        db.close()


@bp.post("")
def upsert_budget() -> tuple:
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        budget_service = BudgetService(db)
        return jsonify(ok(budget_service.upsert(user_id, body))), 200
    finally:
        db.close()
