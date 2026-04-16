import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import QuestionSource, QuestionType, ReviewStatus


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    difficulty: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    question_type: Mapped[QuestionType | None] = mapped_column(
        # PRD + migration create the Postgres ENUM with lowercase values (e.g. "scenario"),
        # so we must persist Python Enum *values* not member names (e.g. "SCENARIO").
        SQLEnum(QuestionType, name="question_type", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSONB, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(10), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_concepts: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    source: Mapped[QuestionSource | None] = mapped_column(
        SQLEnum(QuestionSource, name="question_source", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    review_status: Mapped[ReviewStatus | None] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    times_answered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    times_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
