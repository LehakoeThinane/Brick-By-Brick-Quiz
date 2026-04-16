import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.adaptive_selector import priority_score
from app.models.answer_attempt import AnswerAttempt
from app.models.enums import MasteryState, QuizMode, ReviewStatus
from app.models.mastery_profile import MasteryProfile
from app.models.question import Question
from app.models.quiz_session import QuizSession
from app.models.review_queue import ReviewQueue


def _fetch_last_seen_map(db: Session, user_id: uuid.UUID) -> dict[uuid.UUID, datetime]:
    rows = db.execute(
        select(AnswerAttempt.question_id, func.max(AnswerAttempt.answered_at))
        .where(AnswerAttempt.user_id == user_id, AnswerAttempt.question_id.is_not(None))
        .group_by(AnswerAttempt.question_id)
    ).all()
    return {row[0]: row[1] for row in rows if row[0] is not None and row[1] is not None}


def _fetch_user_avg_difficulty_by_category(db: Session, user_id: uuid.UUID) -> dict[uuid.UUID, float]:
    rows = db.execute(
        select(Question.category_id, func.avg(Question.difficulty))
        .join(AnswerAttempt, AnswerAttempt.question_id == Question.id)
        .where(
            AnswerAttempt.user_id == user_id,
            Question.category_id.is_not(None),
            Question.difficulty.is_not(None),
        )
        .group_by(Question.category_id)
    ).all()
    return {row[0]: float(row[1]) for row in rows if row[0] is not None and row[1] is not None}


def _fetch_profile_state_by_category(db: Session, user_id: uuid.UUID) -> dict[uuid.UUID, MasteryState]:
    rows = db.execute(
        select(MasteryProfile.category_id, MasteryProfile.mastery_state).where(
            MasteryProfile.user_id == user_id,
            MasteryProfile.category_id.is_not(None),
            MasteryProfile.mastery_state.is_not(None),
        )
    ).all()
    return {row[0]: row[1] for row in rows if row[0] is not None}


def _fetch_session_served_categories(db: Session, session_id: uuid.UUID) -> set[uuid.UUID]:
    rows = db.execute(
        select(Question.category_id)
        .join(AnswerAttempt, AnswerAttempt.question_id == Question.id)
        .where(
            AnswerAttempt.session_id == session_id,
            Question.category_id.is_not(None),
        )
        .distinct()
    ).all()
    return {row[0] for row in rows if row[0] is not None}


def _fetch_struggling_categories(db: Session, user_id: uuid.UUID) -> set[uuid.UUID]:
    rows = db.execute(
        select(MasteryProfile.category_id).where(
            MasteryProfile.user_id == user_id,
            MasteryProfile.mastery_state == MasteryState.STRUGGLING,
            MasteryProfile.category_id.is_not(None),
        )
    ).all()
    return {row[0] for row in rows if row[0] is not None}


def _score_question_candidates(
    *,
    questions: list[Question],
    now: datetime,
    last_seen_map: dict[uuid.UUID, datetime],
    avg_difficulty_map: dict[uuid.UUID, float],
    state_map: dict[uuid.UUID, MasteryState],
) -> list[tuple[Question, float]]:
    scored: list[tuple[Question, float]] = []
    for question in questions:
        category_id = question.category_id
        state = MasteryState.UNSEEN
        user_avg_difficulty = None
        if category_id is not None:
            state = state_map.get(category_id, MasteryState.UNSEEN)
            user_avg_difficulty = avg_difficulty_map.get(category_id)

        score = priority_score(
            mastery_state=state,
            last_seen_at=last_seen_map.get(question.id),
            now=now,
            user_avg_difficulty=user_avg_difficulty,
            question_difficulty=question.difficulty,
        )
        scored.append((question, score))

    scored.sort(key=lambda pair: (pair[1], pair[0].updated_at, pair[0].created_at), reverse=True)
    return scored


def select_next_question(
    db: Session,
    *,
    session: QuizSession,
    answered_question_ids: set[uuid.UUID],
) -> Question | None:
    if session.user_id is None:
        return None

    base_questions_stmt = select(Question).where(Question.review_status == ReviewStatus.APPROVED)

    if answered_question_ids:
        base_questions_stmt = base_questions_stmt.where(Question.id.not_in(answered_question_ids))

    if session.mode == QuizMode.CATEGORY and session.category_id is not None:
        base_questions_stmt = base_questions_stmt.where(Question.category_id == session.category_id)

    if session.mode == QuizMode.REVIEW:
        review_stmt = (
            select(ReviewQueue, Question)
            .join(Question, Question.id == ReviewQueue.question_id)
            .where(
                ReviewQueue.user_id == session.user_id,
                ReviewQueue.reviewed_at.is_(None),
                Question.review_status == ReviewStatus.APPROVED,
            )
            .order_by(ReviewQueue.priority_score.desc(), ReviewQueue.added_at.asc())
        )
        if answered_question_ids:
            review_stmt = review_stmt.where(Question.id.not_in(answered_question_ids))

        queue_rows = db.execute(review_stmt).all()
        if not queue_rows:
            return None
        return queue_rows[0][1]

    candidates = db.scalars(base_questions_stmt).all()
    if not candidates:
        return None

    now = datetime.utcnow()
    last_seen_map = _fetch_last_seen_map(db, session.user_id)
    avg_difficulty_map = _fetch_user_avg_difficulty_by_category(db, session.user_id)
    state_map = _fetch_profile_state_by_category(db, session.user_id)

    struggling_categories = _fetch_struggling_categories(db, session.user_id)
    served_categories = _fetch_session_served_categories(db, session.id)
    pending_struggling = struggling_categories - served_categories

    if pending_struggling:
        struggling_candidates = [q for q in candidates if q.category_id in pending_struggling]
        if struggling_candidates:
            return _score_question_candidates(
                questions=struggling_candidates,
                now=now,
                last_seen_map=last_seen_map,
                avg_difficulty_map=avg_difficulty_map,
                state_map=state_map,
            )[0][0]

    scored = _score_question_candidates(
        questions=candidates,
        now=now,
        last_seen_map=last_seen_map,
        avg_difficulty_map=avg_difficulty_map,
        state_map=state_map,
    )
    return scored[0][0] if scored else None
