from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.progress import ProgressSummaryResponse
from app.services.auth_service import get_current_user
from app.services.progress_service import get_progress_summary

router = APIRouter(prefix="/users", tags=["progress"])


@router.get("/me/progress", response_model=ProgressSummaryResponse)
def get_my_progress_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ProgressSummaryResponse:
    return get_progress_summary(db, user_id=current_user.id)
