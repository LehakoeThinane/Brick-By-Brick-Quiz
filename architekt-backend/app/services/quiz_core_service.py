import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.domain.answer_evaluator import AnswerEvaluation, evaluate_answer
from app.domain.mastery_state_machine import MasteryStats, transition_mastery_state
from app.models.answer_attempt import AnswerAttempt
from app.models.category import Category
from app.models.enums import MasteryState, QuizSessionStatus
from app.models.mastery_profile import MasteryProfile
from app.models.question import Question
from app.models.quiz_session import QuizSession
from app.models.review_queue import ReviewQueue


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_options(options: dict[str, Any] | list[Any] | None) -> dict[str, Any] | list[Any]:
    """
    Convert question options into the PRD-friendly canonical form:
    - Input: { "A": "text", "B": "text", ... }
    - Output: [ { "key": "A", "text": "text" }, ... ]
    """
    if options is None:
        return []

    if isinstance(options, dict):
        def to_text(v: Any) -> str:
            if isinstance(v, str):
                return v
            if isinstance(v, dict) and "text" in v:
                return str(v["text"])
            return str(v)

        # Sort by option key for deterministic ordering (A..D)
        return [{"key": k, "text": to_text(v)} for k, v in sorted(options.items(), key=lambda kv: kv[0])]

    return options


def evaluate_and_store_attempt(
    db: Session,
    *,
    user_id: uuid.UUID,
    question: Question,
    submitted_answer: str,
    response_time_ms: int,
    question_version: int,
    session_id: uuid.UUID | None,
) -> tuple[AnswerAttempt, AnswerEvaluation]:
    evaluation = evaluate_answer(submitted_answer, question.correct_answer, response_time_ms)

    attempt = AnswerAttempt(
        id=uuid.uuid4(),
        session_id=session_id,
        user_id=user_id,
        question_id=question.id,
        question_version=question_version,
        submitted_answer=submitted_answer.strip().upper(),
        correct_answer=question.correct_answer,
        is_correct=evaluation.is_correct,
        response_time_ms=response_time_ms,
        mastery_signal=evaluation.mastery_signal,
        answered_at=utc_now_naive(),
    )
    db.add(attempt)

    question.times_answered = (question.times_answered or 0) + 1
    if evaluation.is_correct:
        question.times_correct = (question.times_correct or 0) + 1

    if evaluation.is_correct:
        pending_review_items = db.scalars(
            select(ReviewQueue).where(
                ReviewQueue.user_id == user_id,
                ReviewQueue.question_id == question.id,
                ReviewQueue.reviewed_at.is_(None),
            )
        ).all()
        reviewed_at = utc_now_naive()
        for item in pending_review_items:
            item.reviewed_at = reviewed_at
            db.add(item)

    profile = update_mastery_profile(db, user_id=user_id, category_id=question.category_id)

    if session_id is not None and evaluation.is_correct:
        session = db.scalar(select(QuizSession).where(QuizSession.id == session_id))
        if session is not None:
            session.correct_count = (session.correct_count or 0) + 1
            db.add(session)

    db.add(question)
    if profile is not None:
        db.add(profile)
    return attempt, evaluation


def update_mastery_profile(
    db: Session,
    *,
    user_id: uuid.UUID,
    category_id: uuid.UUID | None,
) -> MasteryProfile | None:
    if category_id is None:
        return None

    profile = db.scalar(
        select(MasteryProfile).where(
            MasteryProfile.user_id == user_id,
            MasteryProfile.category_id == category_id,
        )
    )

    if profile is None:
        profile = MasteryProfile(
            id=uuid.uuid4(),
            user_id=user_id,
            category_id=category_id,
            mastery_state=MasteryState.UNSEEN,
            total_attempts=0,
            correct_count=0,
            rolling_accuracy=None,
            avg_response_time_ms=None,
            consecutive_correct=0,
            last_attempted_at=None,
            updated_at=utc_now_naive(),
        )
        db.add(profile)
        db.flush()

    recent_attempts = db.execute(
        select(AnswerAttempt.is_correct, AnswerAttempt.response_time_ms, AnswerAttempt.answered_at)
        .join(Question, Question.id == AnswerAttempt.question_id)
        .where(
            AnswerAttempt.user_id == user_id,
            Question.category_id == category_id,
        )
        .order_by(AnswerAttempt.answered_at.desc())
        .limit(10)
    ).all()

    attempts_last_10 = len(recent_attempts)
    attempts_last_5 = min(attempts_last_10, 5)

    correct_last_10 = sum(1 for row in recent_attempts if row.is_correct)
    correct_last_5 = sum(1 for row in recent_attempts[:attempts_last_5] if row.is_correct)

    accuracy_last_10 = None if attempts_last_10 == 0 else (correct_last_10 / attempts_last_10) * 100
    accuracy_last_5 = None if attempts_last_5 == 0 else (correct_last_5 / attempts_last_5) * 100

    avg_response_time_ms = None
    if attempts_last_10 > 0:
        avg_response_time_ms = int(sum(row.response_time_ms for row in recent_attempts) / attempts_last_10)

    consecutive_correct = 0
    for row in recent_attempts:
        if row.is_correct:
            consecutive_correct += 1
        else:
            break

    totals = db.execute(
        select(
            func.count(AnswerAttempt.id),
            func.sum(case((AnswerAttempt.is_correct.is_(True), 1), else_=0)),
            func.max(AnswerAttempt.answered_at),
        )
        .join(Question, Question.id == AnswerAttempt.question_id)
        .where(
            AnswerAttempt.user_id == user_id,
            Question.category_id == category_id,
        )
    ).one()

    total_attempts = int(totals[0] or 0)
    total_correct = int(totals[1] or 0)
    last_attempted_at = totals[2]

    stats = MasteryStats(
        attempts_last_5=attempts_last_5,
        attempts_last_10=attempts_last_10,
        accuracy_last_5=accuracy_last_5,
        accuracy_last_10=accuracy_last_10,
        consecutive_correct=consecutive_correct,
        avg_response_time_ms=avg_response_time_ms,
        total_attempts=total_attempts,
    )

    profile.mastery_state = transition_mastery_state(profile.mastery_state or MasteryState.UNSEEN, stats)
    profile.total_attempts = total_attempts
    profile.correct_count = total_correct
    profile.rolling_accuracy = None if accuracy_last_10 is None else round(accuracy_last_10, 2)
    profile.avg_response_time_ms = avg_response_time_ms
    profile.consecutive_correct = consecutive_correct
    profile.last_attempted_at = last_attempted_at
    profile.updated_at = utc_now_naive()
    return profile


def get_or_expire_active_session(db: Session, *, session_id: uuid.UUID, user_id: uuid.UUID) -> QuizSession | None:
    session = db.scalar(
        select(QuizSession).where(
            QuizSession.id == session_id,
            QuizSession.user_id == user_id,
        )
    )
    if session is None:
        return None

    now = utc_now_naive()
    if session.status != QuizSessionStatus.ACTIVE:
        return session

    if session.expires_at <= now:
        # PRD: expired sessions are treated like completed sessions for reinforcement loops.
        # Rebuild review queue from the user's mastery state at the moment of expiry.
        from app.services.review_queue_service import rebuild_review_queue

        session.status = QuizSessionStatus.EXPIRED
        session.completed_at = now
        db.add(session)
        rebuild_review_queue(db, user_id=user_id)
        db.commit()

        return session

    # PRD: sessions expire after 60 minutes of inactivity, so each activity extends the expiry window.
    session.expires_at = now + timedelta(minutes=60)
    db.add(session)
    db.commit()
    return session


def complete_session(db: Session, session: QuizSession) -> None:
    session.status = QuizSessionStatus.COMPLETED
    session.completed_at = utc_now_naive()
    db.add(session)


def fetch_session_answered_question_ids(db: Session, session_id: uuid.UUID) -> set[uuid.UUID]:
    rows = db.scalars(
        select(AnswerAttempt.question_id).where(
            AnswerAttempt.session_id == session_id,
            AnswerAttempt.question_id.is_not(None),
        )
    ).all()
    return {row for row in rows if row is not None}


def fetch_session_attempt_count(db: Session, session_id: uuid.UUID) -> int:
    return int(
        db.scalar(select(func.count(AnswerAttempt.id)).where(AnswerAttempt.session_id == session_id)) or 0
    )


def build_weak_topic_names(db: Session, *, user_id: uuid.UUID) -> list[str]:
    rows = db.execute(
        select(Category.name)
        .join(MasteryProfile, MasteryProfile.category_id == Category.id)
        .where(
            MasteryProfile.user_id == user_id,
            MasteryProfile.mastery_state.in_([MasteryState.STRUGGLING, MasteryState.DEVELOPING]),
        )
        .order_by(Category.name.asc())
    ).all()
    return [row[0] for row in rows]


def new_session_expiry() -> datetime:
    return utc_now_naive() + timedelta(minutes=60)
