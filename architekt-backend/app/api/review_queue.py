from fastapi import APIRouter, Depends
import uuid
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.review_queue import (
    ReviewQueueAnswerRequest,
    ReviewQueueAnswerResponse,
    ReviewQueueItem,
    ReviewQueueSummaryResponse,
)
from app.services.auth_service import get_current_user
from app.services.review_answer_service import answer_review_queue_item, get_review_queue, get_review_queue_summary

router = APIRouter(prefix="/review-queue", tags=["review-queue"])


@router.get("", response_model=list[ReviewQueueItem])
def get_review_queue_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[ReviewQueueItem]:
    return get_review_queue(db, user_id=current_user.id)


@router.get("/summary", response_model=ReviewQueueSummaryResponse)
def get_review_queue_summary_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ReviewQueueSummaryResponse:
    return get_review_queue_summary(db, user_id=current_user.id)


@router.post("/{item_id}/answer", response_model=ReviewQueueAnswerResponse)
def answer_review_queue_item_endpoint(
    item_id: uuid.UUID,
    payload: ReviewQueueAnswerRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ReviewQueueAnswerResponse:
    return answer_review_queue_item(
        db,
        user_id=current_user.id,
        item_id=item_id,
        submitted_answer=payload.submitted_answer,
        response_time_ms=payload.response_time_ms,
    )
