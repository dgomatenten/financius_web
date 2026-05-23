from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class SyncEvent(Base):
    __tablename__ = "sync_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    device_id: Mapped[str] = mapped_column(String, nullable=False)
    sync_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sync_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, default="success")
    receipts_count: Mapped[int] = mapped_column(Integer, default=0)
    line_items_count: Mapped[int] = mapped_column(Integer, default=0)
    categories_count: Mapped[int] = mapped_column(Integer, default=0)
    shops_count: Mapped[int] = mapped_column(Integer, default=0)
    cards_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicates_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
