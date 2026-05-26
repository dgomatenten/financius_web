from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func

from config.database import SessionLocal
from models.budget import Budget
from models.receipt import Receipt
from utils.exceptions import ValidationError

MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
VALID_MODES = {"manual", "forecast", "forecast_adjusted"}


class BudgetService:
    def __init__(self, db_session=None) -> None:
        self.db = db_session or SessionLocal

    def list_for_month(self, user_id: str, month: str) -> list[dict[str, object]]:
        self._validate_month(month)
        budgets = (
            self.db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.year_month == month)
            .order_by(Budget.category_id.isnot(None), Budget.category_id)
            .all()
        )
        return [self._serialize(b) for b in budgets]

    def upsert(self, user_id: str, payload: dict[str, object]) -> dict[str, object]:
        month = str(payload.get("month") or payload.get("yearMonth") or "").strip()
        self._validate_month(month)

        category_id = payload.get("categoryId")
        if category_id is not None:
            category_id = str(category_id).strip() or None

        mode = str(payload.get("mode") or "manual").strip()
        if mode not in VALID_MODES:
            raise ValidationError("mode must be one of manual, forecast, forecast_adjusted")

        amount = self._to_float(payload.get("amount"), "amount")
        if amount < 0:
            raise ValidationError("amount must be non-negative")

        adjustment_pct = payload.get("adjustmentPct")
        if adjustment_pct is not None:
            adjustment_pct = int(adjustment_pct)
            if adjustment_pct < 80 or adjustment_pct > 120:
                raise ValidationError("adjustmentPct must be between 80 and 120")

        if mode == "forecast_adjusted" and adjustment_pct is None:
            raise ValidationError("adjustmentPct is required for forecast_adjusted mode")

        if mode in {"forecast", "forecast_adjusted"}:
            base = self._trailing_average(user_id, category_id, month)
            if base is None:
                base = amount
            if mode == "forecast_adjusted":
                amount = round(base * (adjustment_pct / 100.0), 2)
            else:
                amount = round(base, 2)

        rollover_enabled = bool(payload.get("rolloverEnabled", False))
        rollover_balance = (
            round(self._compute_rollover_balance(user_id, month, category_id), 2)
            if rollover_enabled
            else 0.0
        )

        budget = self._find_budget(user_id, month, category_id)
        if not budget:
            budget = Budget(
                id=str(uuid4()),
                user_id=user_id,
                year_month=month,
                category_id=category_id,
            )
            self.db.add(budget)

        budget.mode = mode
        budget.amount = amount
        budget.adjustment_pct = adjustment_pct
        budget.rollover_enabled = rollover_enabled
        budget.rollover_balance = rollover_balance

        self.db.commit()
        self.db.refresh(budget)
        return self._serialize(budget)

    def _validate_month(self, month: str) -> None:
        if not MONTH_PATTERN.match(month):
            raise ValidationError("month must be YYYY-MM")

    def _month_start(self, month: str) -> datetime:
        year, mon = month.split("-")
        return datetime(int(year), int(mon), 1, tzinfo=UTC)

    def _next_month(self, month: str) -> str:
        year, mon = [int(v) for v in month.split("-")]
        mon += 1
        if mon == 13:
            year += 1
            mon = 1
        return f"{year:04d}-{mon:02d}"

    def _previous_month(self, month: str) -> str:
        year, mon = [int(v) for v in month.split("-")]
        mon -= 1
        if mon == 0:
            year -= 1
            mon = 12
        return f"{year:04d}-{mon:02d}"

    def _find_budget(self, user_id: str, month: str, category_id: str | None) -> Budget | None:
        query = self.db.query(Budget).filter(Budget.user_id == user_id, Budget.year_month == month)
        if category_id is None:
            query = query.filter(Budget.category_id.is_(None))
        else:
            query = query.filter(Budget.category_id == category_id)
        return query.first()

    def _trailing_average(self, user_id: str, category_id: str | None, month: str) -> float | None:
        month_start = self._month_start(month)
        window_start_month = month
        for _ in range(3):
            window_start_month = self._previous_month(window_start_month)
        window_start = self._month_start(window_start_month)

        query = self.db.query(func.sum(Receipt.total_amount)).filter(
            Receipt.user_id == user_id,
            Receipt.receipt_date >= window_start,
            Receipt.receipt_date < month_start,
        )
        if category_id is None:
            query = query.filter(Receipt.category_id.is_(None))
        else:
            query = query.filter(Receipt.category_id == category_id)

        total = query.scalar() or 0
        if total <= 0:
            return None
        return float(total) / 3.0

    def _month_spend(self, user_id: str, month: str, category_id: str | None) -> float:
        month_start = self._month_start(month)
        next_month_start = self._month_start(self._next_month(month))
        query = self.db.query(func.sum(Receipt.total_amount)).filter(
            Receipt.user_id == user_id,
            Receipt.receipt_date >= month_start,
            Receipt.receipt_date < next_month_start,
        )
        if category_id is None:
            query = query.filter(Receipt.category_id.is_(None))
        else:
            query = query.filter(Receipt.category_id == category_id)
        return float(query.scalar() or 0.0)

    def _compute_rollover_balance(self, user_id: str, month: str, category_id: str | None) -> float:
        prev_month = self._previous_month(month)
        prev_budget = self._find_budget(user_id, prev_month, category_id)
        if not prev_budget or not prev_budget.rollover_enabled:
            return 0.0
        prev_spent = self._month_spend(user_id, prev_month, category_id)
        available_prev = float(prev_budget.amount or 0.0) + float(prev_budget.rollover_balance or 0.0)
        return available_prev - prev_spent

    def _to_float(self, value: object, field: str) -> float:
        try:
            return float(value if value is not None else 0)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{field} must be a number") from exc

    def _serialize(self, budget: Budget) -> dict[str, object]:
        return {
            "id": budget.id,
            "month": budget.year_month,
            "categoryId": budget.category_id,
            "mode": budget.mode,
            "amount": round(float(budget.amount or 0.0), 2),
            "adjustmentPct": budget.adjustment_pct,
            "rolloverEnabled": bool(budget.rollover_enabled),
            "rolloverBalance": round(float(budget.rollover_balance or 0.0), 2),
        }
