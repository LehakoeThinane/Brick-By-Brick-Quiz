import uuid

from pydantic import BaseModel, Field

from app.models.enums import MasterySignal


class AnswerSubmitRequest(BaseModel):
    question_id: uuid.UUID
    question_version: int
    submitted_answer: str = Field(min_length=1, max_length=10)
    response_time_ms: int = Field(ge=0)


class AnswerEvaluationResponse(BaseModel):
    question_id: uuid.UUID
    is_correct: bool
    correct_answer: str
    explanation: str
    mastery_signal: MasterySignal
    response_time_ms: int
