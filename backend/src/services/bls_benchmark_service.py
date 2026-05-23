from repositories.analytics_repository import AnalyticsRepository


class BLSBenchmarkService:
    # Lightweight placeholder benchmark shares for v1; replace with live BLS dataset later.
    _BENCHMARK_SHARES = {
        "Housing": 33.0,
        "Food": 12.0,
        "Transportation": 16.0,
        "Healthcare": 8.0,
        "Entertainment": 5.0,
        "Uncategorized": 0.0,
    }

    def __init__(self, db_session=None) -> None:
        self.repository = AnalyticsRepository(db_session)

    def compare(self, user_id: str, period: str, currency: str) -> dict[str, object]:
        categories = self.repository.category_breakdown(user_id, period, currency)
        total = sum(float(c.get("amount") or 0.0) for c in categories)

        items = []
        for cat in categories:
            name = str(cat.get("name") or "Uncategorized")
            amount = float(cat.get("amount") or 0.0)
            user_share = (amount / total * 100.0) if total > 0 else 0.0
            benchmark_share = float(self._BENCHMARK_SHARES.get(name, 0.0))
            delta = user_share - benchmark_share
            items.append(
                {
                    "name": name,
                    "amount": round(amount, 2),
                    "userSharePct": round(user_share, 2),
                    "benchmarkSharePct": round(benchmark_share, 2),
                    "deltaPct": round(delta, 2),
                }
            )

        return {"period": period, "currency": currency, "items": items}
