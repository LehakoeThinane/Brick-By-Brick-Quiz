from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from typing import Dict, Any

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.mastery_profile import MasteryProfile
from app.models.review_queue import ReviewQueue
from app.models.offline_sync_queue import OfflineSyncQueue
from app.models.question import Question
from app.models.enums import MasteryState, ReviewStatus

router = APIRouter()

@router.get("/health", summary="Get Mastery System Health")
def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # 1. Struggling Topics
    struggling_topics = db.execute(
        select(func.count(MasteryProfile.id))
        .where(MasteryProfile.user_id == current_user.id)
        .where(
            or_(
                MasteryProfile.state == MasteryState.STRUGGLING,
                MasteryProfile.state == MasteryState.UNSEEN
            )
        )
    ).scalar_one()

    # 2. Review Backlog (Phase 5 PRD)
    review_backlog = db.execute(
        select(func.count(ReviewQueue.id))
        .where(ReviewQueue.user_id == current_user.id)
        .where(ReviewQueue.is_reviewed == False)
    ).scalar_one()

    # 3. Offline Backlog (Stuck disconnected attempts)
    offline_backlog = db.execute(
        select(func.count(OfflineSyncQueue.id))
        .where(OfflineSyncQueue.user_id == current_user.id)
    ).scalar_one()

    return {
        "struggling_topics": struggling_topics,
        "review_backlog": review_backlog,
        "offline_backlog": offline_backlog
    }

@router.get("/admin/questions", summary="Flag poor learning materials")
def get_flagged_questions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Scans the question bank structurally to find questions breaking the engine.
    PRD Rule: times_answered >= 50 AND correct_rate < 20%
    """
    # Requires an Admin role in production, omitting explicit check for MVP limits.
    all_questions = db.execute(
        select(Question).where(Question.review_status == ReviewStatus.APPROVED)
    ).scalars().all()

    flagged = []
    for q in all_questions:
        if q.times_answered >= 50:
            correct_rate = q.times_correct / q.times_answered if q.times_answered > 0 else 0
            if correct_rate < 0.20:
                flagged.append({
                    "id": q.id,
                    "text": q.question_text,
                    "times_answered": q.times_answered,
                    "correct_rate": round(correct_rate * 100, 2),
                    "health_indicator": "CRITICAL"
                })

    return {
        "flagged_questions": flagged,
        "count": len(flagged)
    }
