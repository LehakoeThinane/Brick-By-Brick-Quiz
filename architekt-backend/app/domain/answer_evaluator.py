from dataclasses import dataclass

from app.models.enums import MasterySignal


@dataclass(frozen=True)
class AnswerEvaluation:
    is_correct: bool
    mastery_signal: MasterySignal


def evaluate_answer(submitted_answer: str, correct_answer: str, response_time_ms: int) -> AnswerEvaluation:
    is_correct = submitted_answer.strip().upper() == correct_answer.strip().upper()

    if not is_correct:
        return AnswerEvaluation(is_correct=False, mastery_signal=MasterySignal.MISS)

    if response_time_ms <= 20_000:
        return AnswerEvaluation(is_correct=True, mastery_signal=MasterySignal.STRONG)
    if response_time_ms <= 45_000:
        return AnswerEvaluation(is_correct=True, mastery_signal=MasterySignal.PARTIAL)
    return AnswerEvaluation(is_correct=True, mastery_signal=MasterySignal.WEAK)
