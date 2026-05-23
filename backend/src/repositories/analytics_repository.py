from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import and_, func

from config.database import SessionLocal
from models.category import Category
from models.master_data import Shop
from models.receipt import Receipt


class AnalyticsRepository:
    def __init__(self, db_session=None) -> None:
        self.db = db_session or SessionLocal

    def summary(self, user_id: str, period: str, currency: str) -> dict[str, Any]:
        start, end = self._period_bounds(period)
        q = self._receipt_query(user_id, currency, start, end)
        total = float(q.with_entities(func.sum(Receipt.total_amount)).scalar() or 0.0)
        count = int(q.with_entities(func.count(Receipt.id)).scalar() or 0)

        prev_start, prev_end = self._previous_period_bounds(start, end)
        prev_q = self._receipt_query(user_id, currency, prev_start, prev_end)
        prev_total = float(prev_q.with_entities(func.sum(Receipt.total_amount)).scalar() or 0.0)
        mom_pct = ((total - prev_total) / prev_total * 100.0) if prev_total > 0 else 0.0

        top_categories = (
            self.db.query(
                Receipt.category_id,
                func.coalesce(Category.name, "Uncategorized").label("name"),
                func.sum(Receipt.total_amount).label("amount"),
            )
            .outerjoin(Category, and_(Category.id == Receipt.category_id, Category.user_id == user_id))
            .filter(*self._receipt_filters(user_id, currency, start, end))
            .group_by(Receipt.category_id, Category.name)
            .order_by(func.sum(Receipt.total_amount).desc())
            .limit(5)
            .all()
        )

        top_shops = (
            self.db.query(
                Receipt.shop_id,
                func.coalesce(Shop.name, "Unknown Shop").label("name"),
                func.sum(Receipt.total_amount).label("amount"),
            )
            .outerjoin(Shop, and_(Shop.id == Receipt.shop_id, Shop.user_id == user_id))
            .filter(*self._receipt_filters(user_id, currency, start, end))
            .group_by(Receipt.shop_id, Shop.name)
            .order_by(func.sum(Receipt.total_amount).desc())
            .limit(5)
            .all()
        )

        return {
            "period": period,
            "currency": currency,
            "totalSpending": round(total, 2),
            "monthOverMonthPct": round(mom_pct, 2),
            "receiptCount": count,
            "topCategories": [
                {"categoryId": r.category_id, "name": r.name, "amount": round(float(r.amount or 0.0), 2)}
                for r in top_categories
            ],
            "topShops": [
                {"shopId": r.shop_id, "name": r.name, "amount": round(float(r.amount or 0.0), 2)}
                for r in top_shops
            ],
        }

    def category_breakdown(self, user_id: str, period: str, currency: str) -> list[dict[str, Any]]:
        start, end = self._period_bounds(period)
        rows = (
            self.db.query(
                Receipt.category_id,
                func.coalesce(Category.name, "Uncategorized").label("name"),
                func.sum(Receipt.total_amount).label("amount"),
            )
            .outerjoin(Category, and_(Category.id == Receipt.category_id, Category.user_id == user_id))
            .filter(*self._receipt_filters(user_id, currency, start, end))
            .group_by(Receipt.category_id, Category.name)
            .order_by(func.sum(Receipt.total_amount).desc())
            .all()
        )
        return [
            {
                "categoryId": r.category_id,
                "name": r.name,
                "amount": round(float(r.amount or 0.0), 2),
            }
            for r in rows
        ]

    def calendar(self, user_id: str, period: str, currency: str) -> list[dict[str, Any]]:
        start, end = self._period_bounds(period)
        rows = (
            self.db.query(
                func.date(Receipt.receipt_date).label("day"),
                func.sum(Receipt.total_amount).label("amount"),
                func.count(Receipt.id).label("receiptCount"),
            )
            .filter(*self._receipt_filters(user_id, currency, start, end))
            .group_by(func.date(Receipt.receipt_date))
            .order_by(func.date(Receipt.receipt_date).asc())
            .all()
        )
        return [
            {
                "day": str(r.day),
                "amount": round(float(r.amount or 0.0), 2),
                "receiptCount": int(r.receiptCount or 0),
            }
            for r in rows
        ]

    def yoy(self, user_id: str, period: str, currency: str) -> list[dict[str, Any]]:
        start, end = self._period_bounds(period)
        span_days = max((end - start).days, 1)
        prev_end = start
        prev_start = prev_end - (end - start)

        current_rows = (
            self.db.query(Receipt.category_id, func.sum(Receipt.total_amount).label("amount"))
            .filter(*self._receipt_filters(user_id, currency, start, end))
            .group_by(Receipt.category_id)
            .all()
        )
        prev_rows = (
            self.db.query(Receipt.category_id, func.sum(Receipt.total_amount).label("amount"))
            .filter(*self._receipt_filters(user_id, currency, prev_start, prev_end))
            .group_by(Receipt.category_id)
            .all()
        )
        current_map = {r.category_id: float(r.amount or 0.0) for r in current_rows}
        prev_map = {r.category_id: float(r.amount or 0.0) for r in prev_rows}
        category_ids = set(current_map) | set(prev_map)

        category_ids_without_none = [cid for cid in category_ids if cid is not None]
        names = (
            {
                row.id: row.name
                for row in self.db.query(Category.id, Category.name)
                .filter(Category.user_id == user_id, Category.id.in_(category_ids_without_none))
                .all()
            }
            if category_ids_without_none
            else {}
        )

        items = []
        for category_id in sorted(category_ids, key=lambda v: names.get(v, "Uncategorized")):
            cur = current_map.get(category_id, 0.0)
            prev = prev_map.get(category_id, 0.0)
            pct = ((cur - prev) / prev * 100.0) if prev > 0 else 0.0
            items.append(
                {
                    "categoryId": category_id,
                    "name": names.get(category_id, "Uncategorized"),
                    "current": round(cur, 2),
                    "previous": round(prev, 2),
                    "changePct": round(pct, 2),
                    "windowDays": span_days,
                }
            )
        return items

    def _receipt_query(self, user_id: str, currency: str, start: datetime, end: datetime):
        return self.db.query(Receipt).filter(*self._receipt_filters(user_id, currency, start, end))

    def _receipt_filters(self, user_id: str, currency: str, start: datetime, end: datetime):
        filters = [Receipt.user_id == user_id, Receipt.receipt_date >= start, Receipt.receipt_date < end]
        if currency:
            filters.append(Receipt.currency == currency)
        return filters

    def _period_bounds(self, period: str) -> tuple[datetime, datetime]:
        now = datetime.now(tz=timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        def shift_months(dt: datetime, delta: int) -> datetime:
            year = dt.year
            month = dt.month + delta
            while month <= 0:
                month += 12
                year -= 1
            while month > 12:
                month -= 12
                year += 1
            return datetime(year, month, 1, tzinfo=timezone.utc)

        if period == "this_month":
            return month_start, shift_months(month_start, 1)
        if period == "last_month":
            start = shift_months(month_start, -1)
            return start, month_start
        if period == "m3":
            return shift_months(month_start, -2), shift_months(month_start, 1)
        if period == "m6":
            return shift_months(month_start, -5), shift_months(month_start, 1)
        if period in {"m12", "custom"}:
            return shift_months(month_start, -11), shift_months(month_start, 1)
        if period == "ytd":
            start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
            return start, shift_months(month_start, 1)
        return month_start, shift_months(month_start, 1)

    def _previous_period_bounds(self, start: datetime, end: datetime) -> tuple[datetime, datetime]:
        delta = end - start
        prev_end = start
        prev_start = start - delta
        return prev_start, prev_end
