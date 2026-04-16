import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.question import QuestionCreate, QuestionRead
from app.services.question_service import create_question, get_approved_question_by_id, list_approved_questions

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question_endpoint(payload: QuestionCreate, db: Session = Depends(get_db)) -> QuestionRead:
    question = create_question(db, payload)
    return QuestionRead.model_validate(question)


@router.get("", response_model=list[QuestionRead])
def list_questions_endpoint(
    category_id: uuid.UUID | None = Query(default=None),
    difficulty: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[QuestionRead]:
    questions = list_approved_questions(db, category_id=category_id, difficulty=difficulty)
    return [QuestionRead.model_validate(question) for question in questions]


@router.get("/{question_id}", response_model=QuestionRead)
def get_question_endpoint(question_id: uuid.UUID, db: Session = Depends(get_db)) -> QuestionRead:
    question = get_approved_question_by_id(db, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return QuestionRead.model_validate(question)
