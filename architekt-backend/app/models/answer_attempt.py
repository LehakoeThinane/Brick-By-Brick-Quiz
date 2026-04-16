import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import MasterySignal, SyncStatus


class AnswerAttempt(Base):
    __tablename__ = "answer_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quiz_sessions.id"), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True
    )
    question_version: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_answer: Mapped[str] = mapped_column(String(10), nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(10), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    mastery_signal: Mapped[MasterySignal | None] = mapped_column(
        SQLEnum(MasterySignal, name="mastery_signal", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    answered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    client_attempt_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), unique=True, nullable=True)
    # PRD/migrations define lowercase enum values (e.g. "pending"), so persist enum *values*.
    # Without this, SQLAlchemy can bind enum member names (e.g. "PENDING").
    sync_status: Mapped[SyncStatus | None] = mapped_column(
        SQLEnum(SyncStatus, name="sync_status", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
