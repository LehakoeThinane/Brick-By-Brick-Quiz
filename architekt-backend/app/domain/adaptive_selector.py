from datetime import datetime

from app.models.enums import MasteryState


def weakness_weight(mastery_state: MasteryState) -> float:
    weights = {
        MasteryState.STRUGGLING: 1.0,
        MasteryState.DEVELOPING: 0.6,
        MasteryState.ATTEMPTED: 0.4,
        MasteryState.COMPETENT: 0.2,
        MasteryState.MASTERED: 0.05,
        MasteryState.UNSEEN: 0.5,
    }
    return weights[mastery_state]


def recency_score(last_seen_at: datetime | None, now: datetime) -> float:
    if last_seen_at is None:
        return 1.0

    days = max((now - last_seen_at).days, 0)
    return min(days / 14.0, 1.0)


def difficulty_match_score(user_avg_difficulty: float | None, question_difficulty: int | None) -> float:
    if user_avg_difficulty is None or question_difficulty is None:
        return 0.5

    difference = abs(user_avg_difficulty - question_difficulty)
    return max(0.0, 1.0 - (difference / 4.0))


def priority_score(
    mastery_state: MasteryState,
    last_seen_at: datetime | None,
    now: datetime,
    user_avg_difficulty: float | None,
    question_difficulty: int | None,
) -> float:
    return (
        weakness_weight(mastery_state) * 0.50
        + recency_score(last_seen_at, now) * 0.30
        + difficulty_match_score(user_avg_difficulty, question_difficulty) * 0.20
    )
