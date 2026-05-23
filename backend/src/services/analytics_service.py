from repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, db_session=None) -> None:
        self.repository = AnalyticsRepository(db_session)

    def summary(self, user_id: str, period: str, currency: str) -> dict[str, object]:
        return self.repository.summary(user_id, period, currency)

    def category_breakdown(self, user_id: str, period: str, currency: str) -> list[dict[str, object]]:
        return self.repository.category_breakdown(user_id, period, currency)

    def calendar(self, user_id: str, period: str, currency: str) -> list[dict[str, object]]:
        return self.repository.calendar(user_id, period, currency)

    def yoy(self, user_id: str, period: str, currency: str) -> list[dict[str, object]]:
        return self.repository.yoy(user_id, period, currency)
