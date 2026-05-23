from sqlalchemy import Boolean, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "year_month", "category_id", name="uq_budget_scope"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    year_month: Mapped[str] = mapped_column(String, nullable=False)
    category_id: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0)
    adjustment_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rollover_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    rollover_balance: Mapped[float] = mapped_column(Float, default=0)
