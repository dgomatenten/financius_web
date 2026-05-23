from flask import Blueprint, jsonify, request

from api.envelope import ok
from config.database import SessionLocal
from services.analytics_service import AnalyticsService
from services.bls_benchmark_service import BLSBenchmarkService
from services.insights_service import InsightsService
from utils.auth import get_current_user_id


bp = Blueprint("analytics", __name__)


def _params() -> tuple[str, str]:
    period = request.args.get("period", "this_month")
    currency = request.args.get("currency", "USD")
    return period, currency


@bp.get("/summary")
def summary() -> tuple:
    user_id = get_current_user_id()
    period, currency = _params()
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        return jsonify(ok(analytics_service.summary(user_id, period, currency))), 200
    finally:
        db.close()


@bp.get("/category-breakdown")
def breakdown() -> tuple:
    user_id = get_current_user_id()
    period, currency = _params()
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        return jsonify(ok({"items": analytics_service.category_breakdown(user_id, period, currency)})), 200
    finally:
        db.close()


@bp.get("/calendar")
def calendar() -> tuple:
    user_id = get_current_user_id()
    period, currency = _params()
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        return jsonify(ok({"days": analytics_service.calendar(user_id, period, currency)})), 200
    finally:
        db.close()


@bp.get("/yoy")
def yoy() -> tuple:
    user_id = get_current_user_id()
    period, currency = _params()
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        return jsonify(ok({"items": analytics_service.yoy(user_id, period, currency)})), 200
    finally:
        db.close()


@bp.get("/benchmarks/bls")
def bls() -> tuple:
    user_id = get_current_user_id()
    period, currency = _params()
    db = SessionLocal()
    try:
        bls_service = BLSBenchmarkService(db)
        return jsonify(ok(bls_service.compare(user_id, period, currency))), 200
    finally:
        db.close()


@bp.get("/insights")
def insights() -> tuple:
    user_id = get_current_user_id()
    period, currency = _params()
    db = SessionLocal()
    try:
        insights_service = InsightsService(db)
        return jsonify(ok(insights_service.metrics(user_id, period, currency))), 200
    finally:
        db.close()
