import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.answer_attempt import AnswerAttempt
from app.models.enums import QuizMode, QuizSessionStatus, ReviewStatus
from app.models.question import Question
from app.models.quiz_session import QuizSession
from app.schemas.answer import AnswerEvaluationResponse, AnswerSubmitRequest
from app.schemas.session import NextQuestionResponse, SessionCreateRequest, SessionCreateResponse, SessionQuestion, SessionResultsResponse
from app.services.adaptive_service import select_next_question
from app.services.quiz_core_service import (
    build_weak_topic_names,
    complete_session,
    evaluate_and_store_attempt,
    fetch_session_answered_question_ids,
    fetch_session_attempt_count,
    get_or_expire_active_session,
    normalize_options,
    new_session_expiry,
    utc_now_naive,
)
from app.services.review_queue_service import rebuild_review_queue


def create_session(db: Session, *, user_id: uuid.UUID, payload: SessionCreateRequest) -> SessionCreateResponse:
    if payload.mode == QuizMode.CATEGORY and payload.category_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="category_id is required for category mode",
        )

    session = QuizSession(
        id=uuid.uuid4(),
        user_id=user_id,
        mode=payload.mode,
        category_id=payload.category_id,
        status=QuizSessionStatus.ACTIVE,
        total_questions=payload.total_questions,
        correct_count=0,
        started_at=utc_now_naive(),
        completed_at=None,
        expires_at=new_session_expiry(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionCreateResponse(
        session_id=session.id,
        mode=session.mode,
        status=session.status,
        total_questions=session.total_questions,
        expires_at=session.expires_at,
    )


def get_next_question(db: Session, *, user_id: uuid.UUID, session_id: uuid.UUID) -> NextQuestionResponse:
    session = get_or_expire_active_session(db, session_id=session_id, user_id=user_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.status != QuizSessionStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Session is {session.status.value}")

    answered_question_ids = fetch_session_answered_question_ids(db, session.id)
    answered_count = fetch_session_attempt_count(db, session.id)

    if answered_count >= session.total_questions:
        complete_session(db, session)
        rebuild_review_queue(db, user_id=user_id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session completed")

    question = select_next_question(db, session=session, answered_question_ids=answered_question_ids)
    if question is None:
        complete_session(db, session)
        rebuild_review_queue(db, user_id=user_id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No question available")

    return NextQuestionResponse(
        session_id=session.id,
        question_number=answered_count + 1,
        total_questions=session.total_questions,
        question=SessionQuestion(
            id=question.id,
            version=question.version,
            category_id=question.category_id,
            subcategory=question.subcategory,
            tags=question.tags,
            difficulty=question.difficulty,
            question_type=question.question_type,
            question_text=question.question_text,
            options=normalize_options(question.options),
            hint=question.hint,
        ),
    )


def submit_answer(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    payload: AnswerSubmitRequest,
) -> AnswerEvaluationResponse:
    session = get_or_expire_active_session(db, session_id=session_id, user_id=user_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.status != QuizSessionStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Session is {session.status.value}")

    question = db.scalar(select(Question).where(Question.id == payload.question_id))
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    if question.review_status != ReviewStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question is not approved")

    prior_attempt_count = int(
        db.scalar(
            select(func.count(AnswerAttempt.id)).where(
                AnswerAttempt.session_id == session.id,
                AnswerAttempt.question_id == payload.question_id,
            )
        )
        or 0
    )
    if prior_attempt_count > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question already answered in this session")

    if question.version != payload.question_version:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Question version mismatch")

    _, evaluation = evaluate_and_store_attempt(
        db,
        user_id=user_id,
        question=question,
        submitted_answer=payload.submitted_answer,
        response_time_ms=payload.response_time_ms,
        question_version=payload.question_version,
        session_id=session.id,
    )

    attempt_count = fetch_session_attempt_count(db, session.id)
    if attempt_count >= session.total_questions:
        complete_session(db, session)
        rebuild_review_queue(db, user_id=user_id)

    db.commit()

    return AnswerEvaluationResponse(
        question_id=question.id,
        is_correct=evaluation.is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        mastery_signal=evaluation.mastery_signal,
        response_time_ms=payload.response_time_ms,
    )


def get_session_results(db: Session, *, user_id: uuid.UUID, session_id: uuid.UUID) -> SessionResultsResponse:
    session = db.scalar(
        select(QuizSession).where(
            QuizSession.id == session_id,
            QuizSession.user_id == user_id,
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    total_answered = fetch_session_attempt_count(db, session.id)
    total_questions = max(session.total_questions, total_answered)
    accuracy = 0.0 if total_answered == 0 else round((session.correct_count / total_answered) * 100, 2)

    weak_topics = build_weak_topic_names(db, user_id=user_id)

    avg_response_time_ms = db.scalar(
        select(func.avg(AnswerAttempt.response_time_ms)).where(AnswerAttempt.session_id == session.id)
    )
    total_time_ms = None
    if session.completed_at is not None and session.started_at is not None:
        total_time_ms = int((session.completed_at - session.started_at).total_seconds() * 1000)

    return SessionResultsResponse(
        session_id=session.id,
        total_questions=total_questions,
        correct_count=session.correct_count,
        accuracy_percent=accuracy,
        weak_topics=weak_topics,
        average_response_time_ms=None if avg_response_time_ms is None else int(avg_response_time_ms),
        total_time_ms=total_time_ms,
    )
