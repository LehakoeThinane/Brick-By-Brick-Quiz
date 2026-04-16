import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import MasteryState


class TopicProgress(BaseModel):
    category_id: uuid.UUID
    category_name: str
    mastery_state: MasteryState
    total_attempts: int
    correct_count: int
    rolling_accuracy: float | None
    avg_response_time_ms: int | None
    consecutive_correct: int
    last_attempted_at: datetime | None


class ProgressSummaryResponse(BaseModel):
    user_id: uuid.UUID
    struggling_topics: int
    developing_topics: int
    mastered_topics: int
    topics: list[TopicProgress]
