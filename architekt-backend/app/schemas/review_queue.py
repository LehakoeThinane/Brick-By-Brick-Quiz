import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import QuestionType


class ReviewQueueItem(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    question_version: int
    category_id: uuid.UUID | None
    subcategory: str | None
    tags: list[str] | None
    difficulty: int | None
    question_type: QuestionType | None
    question_text: str
    options: dict[str, Any] | list[Any]
    hint: str | None
    correct_answer: str
    explanation: str
    priority_score: float
    reason: str | None
    added_at: datetime
    reviewed_at: datetime | None


class ReviewQueueSummaryResponse(BaseModel):
    total_items: int
    pending_items: int
    top_priority_score: float | None


class ReviewQueueAnswerRequest(BaseModel):
    submitted_answer: str = Field(min_length=1, max_length=10)
    response_time_ms: int = Field(ge=0)


class ReviewQueueAnswerResponse(BaseModel):
    item_id: uuid.UUID
    is_correct: bool
    updated_priority_score: float
    reviewed: bool
