import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.answer_attempt import AnswerAttempt
from app.models.category import Category
from app.models.enums import MasteryState, ReviewStatus
from app.models.mastery_profile import MasteryProfile
from app.models.question import Question
from app.models.review_queue import ReviewQueue
from app.services.quiz_core_service import utc_now_naive


def rebuild_review_queue(db: Session, *, user_id: uuid.UUID) -> None:
    db.execute(
        delete(ReviewQueue).where(
            ReviewQueue.user_id == user_id,
            ReviewQueue.reviewed_at.is_(None),
        )
    )

    items_to_insert: list[ReviewQueue] = []
    now = utc_now_naive()

    weak_profiles = db.scalars(
        select(MasteryProfile).where(
            MasteryProfile.user_id == user_id,
            MasteryProfile.rolling_accuracy.is_not(None),
            MasteryProfile.rolling_accuracy < 60,
            MasteryProfile.category_id.is_not(None),
        )
    ).all()

    selected_question_ids: set[uuid.UUID] = set()

    for profile in weak_profiles:
        candidate_question = db.scalar(
            select(Question)
            .where(
                Question.category_id == profile.category_id,
                Question.review_status == ReviewStatus.APPROVED,
            )
            .order_by(Question.updated_at.desc())
            .limit(1)
        )
        if candidate_question is None or candidate_question.id in selected_question_ids:
            continue

        rolling_accuracy = float(profile.rolling_accuracy or 0)
        priority_score = round(0.8 + max(0.0, (60.0 - rolling_accuracy) / 100.0), 3)

        category_name = db.scalar(
            select(Category.name).where(Category.id == profile.category_id)
        ) or "topic"

        items_to_insert.append(
            ReviewQueue(
                id=uuid.uuid4(),
                user_id=user_id,
                question_id=candidate_question.id,
                priority_score=priority_score,
                reason=f"Topic accuracy below 60% ({category_name})",
                added_at=now,
                reviewed_at=None,
            )
        )
        selected_question_ids.add(candidate_question.id)

    attempts = db.execute(
        select(
            AnswerAttempt.question_id,
            AnswerAttempt.is_correct,
            AnswerAttempt.answered_at,
        )
        .where(
            AnswerAttempt.user_id == user_id,
            AnswerAttempt.question_id.is_not(None),
        )
        .order_by(AnswerAttempt.answered_at.desc())
    ).all()

    by_question: dict[uuid.UUID, list[tuple[bool, datetime]]] = {}
    for question_id, is_correct, answered_at in attempts:
        if question_id is None:
            continue
        question_attempts = by_question.setdefault(question_id, [])
        if len(question_attempts) < 3:
            question_attempts.append((bool(is_correct), answered_at))

    for question_id, recent_attempts in by_question.items():
        if question_id in selected_question_ids:
            continue

        incorrect_count = sum(1 for is_correct, _ in recent_attempts if not is_correct)
        if len(recent_attempts) < 3 or incorrect_count < 2:
            continue

        question = db.scalar(
            select(Question).where(
                Question.id == question_id,
                Question.review_status == ReviewStatus.APPROVED,
            )
        )
        if question is None:
            continue

        priority_score = round(1.0 + (incorrect_count * 0.1), 3)
        items_to_insert.append(
            ReviewQueue(
                id=uuid.uuid4(),
                user_id=user_id,
                question_id=question.id,
                priority_score=priority_score,
                reason="Answered incorrectly twice in last three attempts",
                added_at=now,
                reviewed_at=None,
            )
        )
        selected_question_ids.add(question.id)

    items_to_insert.sort(key=lambda item: item.priority_score, reverse=True)
    for item in items_to_insert[:50]:
        db.add(item)


def list_pending_review_items(db: Session, *, user_id: uuid.UUID) -> list[ReviewQueue]:
    return db.scalars(
        select(ReviewQueue)
        .where(
            ReviewQueue.user_id == user_id,
            ReviewQueue.reviewed_at.is_(None),
        )
        .order_by(ReviewQueue.priority_score.desc(), ReviewQueue.added_at.asc())
    ).all()
