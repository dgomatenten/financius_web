from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class AmortizationRule(Base):
    __tablename__ = "amortization_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    months: Mapped[int] = mapped_column(Integer, default=12)
    monthly_amount: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String, default="active")
