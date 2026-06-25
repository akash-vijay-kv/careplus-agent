"""Health profile ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class HealthProfile(Base):
    """Patient health profile with allergies, conditions, and history."""

    __tablename__ = "health_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    allergies: Mapped[list] = mapped_column(JSONB, default=list)
    chronic_conditions: Mapped[list] = mapped_column(JSONB, default=list)
    past_procedures: Mapped[list] = mapped_column(JSONB, default=list)
    family_history: Mapped[list] = mapped_column(JSONB, default=list)
    blood_type: Mapped[str | None] = mapped_column(String(10))
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 1))
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 1))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="health_profile")
