from fastapi import APIRouter, Depends
import uuid
from sqlalchemy.orm import Session

from app.schemas.answer import AnswerEvaluationResponse, AnswerSubmitRequest
from app.schemas.session import NextQuestionResponse, SessionCreateRequest, SessionCreateResponse, SessionResultsResponse
from app.db.session import get_db
from app.services.auth_service import get_current_user
from app.services.session_service import create_session, get_next_question, get_session_results, submit_answer

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionCreateResponse)
def create_session_endpoint(
    payload: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SessionCreateResponse:
    return create_session(db, user_id=current_user.id, payload=payload)


@router.get("/{session_id}/next", response_model=NextQuestionResponse)
def get_next_question_endpoint(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> NextQuestionResponse:
    return get_next_question(db, user_id=current_user.id, session_id=session_id)


@router.post("/{session_id}/answer", response_model=AnswerEvaluationResponse)
def submit_answer_endpoint(
    session_id: uuid.UUID,
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AnswerEvaluationResponse:
    return submit_answer(db, user_id=current_user.id, session_id=session_id, payload=payload)


@router.get("/{session_id}/results", response_model=SessionResultsResponse)
def get_results_endpoint(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SessionResultsResponse:
    return get_session_results(db, user_id=current_user.id, session_id=session_id)
