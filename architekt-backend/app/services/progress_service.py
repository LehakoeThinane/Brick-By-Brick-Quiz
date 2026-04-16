import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import MasteryState
from app.models.mastery_profile import MasteryProfile
from app.schemas.progress import ProgressSummaryResponse, TopicProgress


def get_progress_summary(db: Session, *, user_id: uuid.UUID) -> ProgressSummaryResponse:
    rows = db.execute(
        select(MasteryProfile, Category.name)
        .join(Category, Category.id == MasteryProfile.category_id)
        .where(MasteryProfile.user_id == user_id)
        .order_by(Category.name.asc())
    ).all()

    topics: list[TopicProgress] = []
    state_counts = {
        MasteryState.STRUGGLING: 0,
        MasteryState.DEVELOPING: 0,
        MasteryState.MASTERED: 0,
    }

    for profile, category_name in rows:
        state = profile.mastery_state or MasteryState.UNSEEN
        if state in state_counts:
            state_counts[state] += 1

        topics.append(
            TopicProgress(
                category_id=profile.category_id,
                category_name=category_name,
                mastery_state=state,
                total_attempts=profile.total_attempts,
                correct_count=profile.correct_count,
                rolling_accuracy=float(profile.rolling_accuracy) if profile.rolling_accuracy is not None else None,
                avg_response_time_ms=profile.avg_response_time_ms,
                consecutive_correct=profile.consecutive_correct,
                last_attempted_at=profile.last_attempted_at,
            )
        )

    return ProgressSummaryResponse(
        user_id=user_id,
        struggling_topics=state_counts[MasteryState.STRUGGLING],
        developing_topics=state_counts[MasteryState.DEVELOPING],
        mastered_topics=state_counts[MasteryState.MASTERED],
        topics=topics,
    )
