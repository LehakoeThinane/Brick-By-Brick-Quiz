import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import QuestionSource, QuestionType, ReviewStatus


class QuestionCreate(BaseModel):
    category_id: uuid.UUID | None = None
    subcategory: str | None = None
    tags: list[str] | None = None
    difficulty: int | None = None
    question_type: QuestionType | None = None
    question_text: str
    options: dict[str, Any] | list[Any]
    correct_answer: str
    explanation: str
    hint: str | None = None
    related_concepts: list[str] | None = None
    source: QuestionSource | None = None
    review_status: ReviewStatus = ReviewStatus.DRAFT


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    category_id: uuid.UUID | None
    subcategory: str | None
    tags: list[str] | None
    difficulty: int | None
    question_type: QuestionType | None
    question_text: str
    options: dict[str, Any] | list[Any]
    correct_answer: str
    explanation: str
    hint: str | None
    related_concepts: list[str] | None
    source: QuestionSource | None
    review_status: ReviewStatus | None
    times_answered: int
    times_correct: int
    created_at: datetime
    updated_at: datetime
