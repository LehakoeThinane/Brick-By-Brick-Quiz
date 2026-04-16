import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import MasteryState
from app.models.mastery_profile import MasteryProfile
from app.schemas.progress import ProgressSummaryResponse, TopicProgress


def get_progress_summary(db: Session, *, user_id: uuid.UUID) -> ProgressSummaryResponse:
    categories = db.scalars(select(Category).order_by(Category.name.asc())).all()
    profiles = db.scalars(select(MasteryProfile).where(MasteryProfile.user_id == user_id)).all()
    profile_by_category_id = {p.category_id: p for p in profiles if p.category_id is not None}

    topics: list[TopicProgress] = []
    state_counts = {
        MasteryState.STRUGGLING: 0,
        MasteryState.DEVELOPING: 0,
        MasteryState.MASTERED: 0,
    }

    for category in categories:
        profile = profile_by_category_id.get(category.id)
        state = profile.mastery_state if profile is not None and profile.mastery_state is not None else MasteryState.UNSEEN
        if state in state_counts:
            state_counts[state] += 1

        topics.append(
            TopicProgress(
                category_id=category.id,
                category_name=category.name,
                mastery_state=state,
                total_attempts=profile.total_attempts if profile is not None else 0,
                correct_count=profile.correct_count if profile is not None else 0,
                rolling_accuracy=float(profile.rolling_accuracy) if profile is not None and profile.rolling_accuracy is not None else None,
                avg_response_time_ms=profile.avg_response_time_ms if profile is not None else None,
                consecutive_correct=profile.consecutive_correct if profile is not None else 0,
                last_attempted_at=profile.last_attempted_at if profile is not None else None,
            )
        )

    return ProgressSummaryResponse(
        user_id=user_id,
        struggling_topics=state_counts[MasteryState.STRUGGLING],
        developing_topics=state_counts[MasteryState.DEVELOPING],
        mastered_topics=state_counts[MasteryState.MASTERED],
        topics=topics,
    )
