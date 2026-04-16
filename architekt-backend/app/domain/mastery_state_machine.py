from dataclasses import dataclass

from app.models.enums import MasteryState


@dataclass(frozen=True)
class MasteryStats:
    attempts_last_5: int
    attempts_last_10: int
    accuracy_last_5: float | None
    accuracy_last_10: float | None
    consecutive_correct: int
    avg_response_time_ms: int | None
    total_attempts: int


def transition_mastery_state(current_state: MasteryState, stats: MasteryStats) -> MasteryState:
    if stats.attempts_last_5 > 0 and stats.accuracy_last_5 is not None and stats.accuracy_last_5 < 50:
        return MasteryState.STRUGGLING

    if (
        current_state == MasteryState.STRUGGLING
        and stats.attempts_last_5 > 0
        and stats.accuracy_last_5 is not None
        and stats.accuracy_last_5 >= 50
    ):
        return MasteryState.DEVELOPING

    if (
        current_state in {MasteryState.DEVELOPING, MasteryState.ATTEMPTED}
        and stats.attempts_last_10 > 0
        and stats.accuracy_last_10 is not None
        and stats.accuracy_last_10 >= 80
    ):
        return MasteryState.COMPETENT

    if (
        current_state == MasteryState.COMPETENT
        and stats.attempts_last_10 > 0
        and stats.accuracy_last_10 is not None
        and stats.accuracy_last_10 >= 85
        and stats.consecutive_correct >= 4
        and stats.avg_response_time_ms is not None
        and stats.avg_response_time_ms < 30_000
    ):
        return MasteryState.MASTERED

    if (
        current_state == MasteryState.MASTERED
        and stats.attempts_last_10 > 0
        and stats.accuracy_last_10 is not None
        and stats.accuracy_last_10 < 70
    ):
        return MasteryState.DEVELOPING

    if current_state == MasteryState.UNSEEN and stats.total_attempts >= 1:
        return MasteryState.ATTEMPTED

    return current_state
