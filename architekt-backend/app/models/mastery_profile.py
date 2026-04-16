import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import MasteryState


class MasteryProfile(Base):
    __tablename__ = "mastery_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    mastery_state: Mapped[MasteryState | None] = mapped_column(
        SQLEnum(MasteryState, name="mastery_state"),
        nullable=True,
    )
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rolling_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    avg_response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consecutive_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
