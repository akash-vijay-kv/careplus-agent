"""Blood result ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BloodResult(Base):
    """Blood test result record."""

    __tablename__ = "blood_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    test_type: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_range_low: Mapped[float | None] = mapped_column(Numeric(10, 2))
    reference_range_high: Mapped[float | None] = mapped_column(Numeric(10, 2))
    tested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lab_name: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="blood_results")
