from repositories.analytics_repository import AnalyticsRepository


class InsightsService:
    def __init__(self, db_session=None) -> None:
        self.repository = AnalyticsRepository(db_session)

    def metrics(self, user_id: str, period: str, currency: str) -> dict[str, object]:
        summary = self.repository.summary(user_id, period, currency)
        categories = self.repository.category_breakdown(user_id, period, currency)

        total = float(summary.get("totalSpending") or 0.0)
        receipt_count = int(summary.get("receiptCount") or 0)
        avg_per_receipt = (total / receipt_count) if receipt_count > 0 else 0.0

        top_category = categories[0] if categories else None
        top_share = ((float(top_category.get("amount") or 0.0) / total) * 100.0) if top_category and total > 0 else 0.0

        insights = [
            {"key": "total_spending", "label": "Total Spending", "value": round(total, 2)},
            {"key": "receipt_count", "label": "Receipt Count", "value": receipt_count},
            {"key": "avg_per_receipt", "label": "Avg Per Receipt", "value": round(avg_per_receipt, 2)},
            {"key": "mom_change_pct", "label": "MoM Change %",
             "value": round(float(summary.get("monthOverMonthPct") or 0.0), 2)},
            {
                "key": "top_category",
                "label": "Top Category",
                "value": top_category.get("name") if top_category else "-",
            },
            {"key": "top_category_share_pct", "label": "Top Category Share %", "value": round(top_share, 2)},
        ]

        return {
            "period": period,
            "currency": currency,
            "insights": insights,
        }
