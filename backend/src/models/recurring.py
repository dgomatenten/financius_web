from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class RecurringExpenseTemplate(Base):
    __tablename__ = "recurring_expense_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    expected_amount: Mapped[float] = mapped_column(Float, default=0)
    frequency: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[str] = mapped_column(DateTime, nullable=False)


class RecurringExpenseOccurrence(Base):
    __tablename__ = "recurring_expense_occurrences"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    template_id: Mapped[str] = mapped_column(String, nullable=False)
    due_date: Mapped[str] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String, default="upcoming")
