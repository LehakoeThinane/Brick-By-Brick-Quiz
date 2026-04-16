import uuid
from datetime import datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.enums import ReviewStatus
from app.models.question import Question
from app.schemas.question import QuestionCreate


def create_question(db: Session, payload: QuestionCreate) -> Question:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    question = Question(
        id=uuid.uuid4(),
        version=1,
        category_id=payload.category_id,
        subcategory=payload.subcategory,
        tags=payload.tags,
        difficulty=payload.difficulty,
        question_type=payload.question_type,
        question_text=payload.question_text,
        options=payload.options,
        correct_answer=payload.correct_answer,
        explanation=payload.explanation,
        hint=payload.hint,
        related_concepts=payload.related_concepts,
        source=payload.source,
        review_status=payload.review_status,
        times_answered=0,
        times_correct=0,
        created_at=now,
        updated_at=now,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def list_approved_questions(
    db: Session,
    category_id: uuid.UUID | None = None,
    difficulty: int | None = None,
) -> list[Question]:
    stmt: Select[tuple[Question]] = select(Question).where(
        Question.review_status == ReviewStatus.APPROVED
    )

    if category_id is not None:
        stmt = stmt.where(Question.category_id == category_id)

    if difficulty is not None:
        stmt = stmt.where(Question.difficulty == difficulty)

    return list(db.scalars(stmt.order_by(Question.created_at.desc())).all())


def get_approved_question_by_id(db: Session, question_id: uuid.UUID) -> Question | None:
    stmt: Select[tuple[Question]] = select(Question).where(
        Question.id == question_id,
        Question.review_status == ReviewStatus.APPROVED,
    )
    return db.scalars(stmt).first()
