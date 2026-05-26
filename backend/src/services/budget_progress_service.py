from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy import func

from config.database import SessionLocal
from models.budget import Budget
from models.receipt import Receipt
from utils.exceptions import ValidationError

MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


class BudgetProgressService:
    def __init__(self, db_session=None) -> None:
        self.db = db_session or SessionLocal

    def progress(self, user_id: str, month: str) -> list[dict[str, object]]:
        if not MONTH_PATTERN.match(month):
            raise ValidationError("month must be YYYY-MM")

        budgets = (
            self.db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.year_month == month)
            .order_by(Budget.category_id.isnot(None), Budget.category_id)
            .all()
        )

        return [self._with_progress(user_id, month, b) for b in budgets]

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

    def _spent(self, user_id: str, month: str, category_id: str | None) -> float:
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

    def _with_progress(self, user_id: str, month: str, budget: Budget) -> dict[str, object]:
        budget_amount = float(budget.amount or 0.0)
        rollover_balance = float(budget.rollover_balance or 0.0)
        available = budget_amount + rollover_balance
        spent = self._spent(user_id, month, budget.category_id)
        remaining = available - spent
        progress_pct = (spent / available * 100.0) if available > 0 else 0.0

        return {
            "id": budget.id,
            "month": budget.year_month,
            "categoryId": budget.category_id,
            "mode": budget.mode,
            "amount": round(budget_amount, 2),
            "adjustmentPct": budget.adjustment_pct,
            "rolloverEnabled": bool(budget.rollover_enabled),
            "rolloverBalance": round(rollover_balance, 2),
            "spent": round(spent, 2),
            "remaining": round(remaining, 2),
            "progressPct": round(progress_pct, 2),
        }
