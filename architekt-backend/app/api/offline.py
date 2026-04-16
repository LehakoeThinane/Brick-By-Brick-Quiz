from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Any, List
from pydantic import BaseModel
import uuid
import datetime

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.category import Category
from app.models.question import Question
from app.models.mastery_profile import MasteryProfile
from app.models.enums import ReviewStatus, SyncStatus
from app.models.offline_sync_queue import OfflineSyncQueue

router = APIRouter()

class SyncPayload(BaseModel):
    client_attempt_id: uuid.UUID
    question_id: uuid.UUID
    selected_option: str
    response_time_ms: int
    answered_at: datetime.datetime

class SyncRequest(BaseModel):
    attempts: List[SyncPayload]

@router.get("/bootstrap", summary="Fetch baseline data for offline caching")
def get_offline_bootstrap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    categories = db.execute(select(Category)).scalars().all()
    questions = db.execute(
        select(Question).where(Question.review_status == ReviewStatus.APPROVED)
    ).scalars().all()
    mastery = db.execute(
        select(MasteryProfile).where(MasteryProfile.user_id == current_user.id)
    ).scalars().all()

    return {
        "categories": categories,
        "questions": questions,
        "mastery_profiles": mastery
    }


@router.post("/sync/attempts", summary="Synchronous Offline Attempt Sync Engine")
def sync_offline_attempts(
    payload: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    attempts_data = [attempt.model_dump(mode="json") for attempt in payload.attempts]
    
    from app.services.sync_processor import process_sync_batch
    resolution = process_sync_batch(db, current_user.id, attempts_data)

    return resolution

@router.post("/sync/sweep", summary="Trigger the lightweight fallback sweeper")
def sweep_stuck_offline_queue(
    current_user: User = Depends(get_current_user), # Expect Admin role in prod
    db: Session = Depends(get_db)
):
    from app.services.sync_processor import recover_stuck_attempts
    res = recover_stuck_attempts(db)
    return {"message": "Sweeper finished", "items_swept": res["swept"]}

