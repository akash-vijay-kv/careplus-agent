"""Prescription ORM model."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prescription(Base):
    """Prescription linked to a medication."""

    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    medication_id: Mapped[int] = mapped_column(Integer, ForeignKey("medications.id"), nullable=False)
    prescribing_doctor: Mapped[str] = mapped_column(String(200), nullable=False)
    refills_remaining: Mapped[int] = mapped_column(Integer, default=0)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    pharmacy: Mapped[str | None] = mapped_column(String(200))
    last_refill_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="prescriptions")
    medication = relationship("Medication", back_populates="prescription")
