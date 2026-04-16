import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ReviewStatus
from app.models.question import Question
from app.models.review_queue import ReviewQueue
from app.schemas.review_queue import ReviewQueueAnswerResponse, ReviewQueueItem, ReviewQueueSummaryResponse
from app.services.quiz_core_service import evaluate_and_store_attempt, normalize_options


def get_review_queue(db: Session, *, user_id: uuid.UUID) -> list[ReviewQueueItem]:
    rows = db.execute(
        select(ReviewQueue, Question)
        .join(Question, Question.id == ReviewQueue.question_id)
        .where(
            ReviewQueue.user_id == user_id,
            ReviewQueue.reviewed_at.is_(None),
            Question.review_status == ReviewStatus.APPROVED,
        )
        .order_by(ReviewQueue.priority_score.desc(), ReviewQueue.added_at.asc())
    ).all()

    result: list[ReviewQueueItem] = []
    for queue_item, question in rows:
        result.append(
            ReviewQueueItem(
                id=queue_item.id,
                question_id=queue_item.question_id,
                question_version=question.version,
                category_id=question.category_id,
                subcategory=question.subcategory,
                tags=question.tags,
                difficulty=question.difficulty,
                question_type=question.question_type,
                question_text=question.question_text,
                options=normalize_options(question.options),
                hint=question.hint,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                priority_score=float(queue_item.priority_score),
                reason=queue_item.reason,
                added_at=queue_item.added_at,
                reviewed_at=queue_item.reviewed_at,
            )
        )

    return result


def get_review_queue_summary(db: Session, *, user_id: uuid.UUID) -> ReviewQueueSummaryResponse:
    pending_items = db.scalars(
        select(ReviewQueue).where(
            ReviewQueue.user_id == user_id,
            ReviewQueue.reviewed_at.is_(None),
        )
    ).all()

    total_items = len(pending_items)
    top_priority = None if total_items == 0 else float(max(item.priority_score for item in pending_items))

    return ReviewQueueSummaryResponse(
        total_items=total_items,
        pending_items=total_items,
        top_priority_score=top_priority,
    )


def answer_review_queue_item(
    db: Session,
    *,
    user_id: uuid.UUID,
    item_id: uuid.UUID,
    submitted_answer: str,
    response_time_ms: int,
) -> ReviewQueueAnswerResponse:
    item = db.scalar(
        select(ReviewQueue).where(
            ReviewQueue.id == item_id,
            ReviewQueue.user_id == user_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review queue item not found")
    if item.reviewed_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review queue item already reviewed")

    question = db.scalar(
        select(Question).where(
            Question.id == item.question_id,
            Question.review_status == ReviewStatus.APPROVED,
        )
    )
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    _, evaluation = evaluate_and_store_attempt(
        db,
        user_id=user_id,
        question=question,
        submitted_answer=submitted_answer,
        response_time_ms=response_time_ms,
        question_version=question.version,
        session_id=None,
    )

    if evaluation.is_correct:
        reviewed = True
    else:
        item.priority_score = round(float(item.priority_score) + 0.100, 3)
        reviewed = False

    db.add(item)
    db.commit()

    return ReviewQueueAnswerResponse(
        item_id=item.id,
        is_correct=evaluation.is_correct,
        updated_priority_score=float(item.priority_score),
        reviewed=reviewed,
    )
