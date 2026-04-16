import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import QuestionType, QuizMode, QuizSessionStatus


class SessionCreateRequest(BaseModel):
    mode: QuizMode
    category_id: uuid.UUID | None = None
    total_questions: int = Field(default=10, ge=5, le=30)


class SessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    mode: QuizMode
    status: QuizSessionStatus
    total_questions: int
    expires_at: datetime


class SessionQuestion(BaseModel):
    id: uuid.UUID
    version: int
    category_id: uuid.UUID | None
    subcategory: str | None
    tags: list[str] | None
    difficulty: int | None
    question_type: QuestionType | None
    question_text: str
    options: dict[str, Any] | list[Any]
    hint: str | None


class NextQuestionResponse(BaseModel):
    session_id: uuid.UUID
    question_number: int
    total_questions: int
    question: SessionQuestion


class SessionResultsResponse(BaseModel):
    session_id: uuid.UUID
    total_questions: int
    correct_count: int
    accuracy_percent: float
    weak_topics: list[str]
