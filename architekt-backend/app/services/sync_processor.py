from typing import List, Dict, Any
import uuid
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.answer_attempt import AnswerAttempt
from app.models.question import Question
from app.models.offline_sync_queue import OfflineSyncQueue
from app.models.enums import SyncStatus
from app.domain.answer_evaluator import evaluate_answer
from app.domain.mastery_state_machine import transition_mastery_state


def process_sync_batch(db: Session, user_id: uuid.UUID, attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synchronously processes a batch of offline attempts.
    Validates, dedupes, evaluates, and persists within the request lifecycle.
    """
    results = []
    summary = {
        "received": len(attempts),
        "synced": 0,
        "duplicate": 0,
        "rejected": 0
    }

    for attempt_data in attempts:
        client_attempt_id = attempt_data.get("client_attempt_id")
        
        # Deduplication Check
        existing_attempt = db.execute(
            select(AnswerAttempt).where(AnswerAttempt.client_attempt_id == client_attempt_id)
        ).scalar_one_or_none()

        if existing_attempt:
            results.append({
                "client_attempt_id": client_attempt_id,
                "status": "duplicate"
            })
            summary["duplicate"] += 1
            continue

        # Fetch canonical question data for evaluation
        question_id = attempt_data.get("question_id")
        selected_option = attempt_data.get("selected_option")
        response_time_ms = attempt_data.get("response_time_ms")
        
        question = db.execute(
            select(Question).where(Question.id == question_id)
        ).scalar_one_or_none()

        if not question:
            results.append({
                "client_attempt_id": client_attempt_id,
                "status": "rejected_invalid_question",
                "reason": "Question not found"
            })
            summary["rejected"] += 1
            continue

        # Domain Evaluation
        is_correct = (selected_option == question.correct_answer)
        mastery_signal = evaluate_answer(
            is_correct=is_correct,
            response_time_ms=response_time_ms,
            question_difficulty=question.difficulty
        )

        # Transition Mastery State
        transition_mastery_state(
            db=db,
            user_id=user_id,
            category_id=question.category_id,
            mastery_signal=mastery_signal
        )

        # Build and Persist authoritative Answer Attempt
        new_attempt = AnswerAttempt(
            user_id=user_id,
            question_id=question.id,
            question_version=question.version,
            submitted_answer=selected_option,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
            response_time_ms=response_time_ms,
            mastery_signal=mastery_signal,
            answered_at=attempt_data.get("answered_at"),
            client_attempt_id=client_attempt_id,
            sync_status=SyncStatus.SYNCED,
            synced_at=datetime.datetime.utcnow()
        )
        
        db.add(new_attempt)
        
        # Remove from fallback queue if it was stuck there
        stuck_queue_item = db.execute(
            select(OfflineSyncQueue).where(OfflineSyncQueue.client_attempt_id == client_attempt_id)
        ).scalar_one_or_none()
        if stuck_queue_item:
            db.delete(stuck_queue_item)

        results.append({
            "client_attempt_id": client_attempt_id,
            "status": "synced"
        })
        summary["synced"] += 1

    db.commit()

    return {
        "results": results,
        "summary": summary
    }

def recover_stuck_attempts(db: Session) -> Dict[str, Any]:
    """
    Fallback sweeper job to re-process offline_sync_queue records
    that were stranded/interrupted and belong to users.
    """
    stuck_records = db.execute(
        select(OfflineSyncQueue).where(OfflineSyncQueue.status == SyncStatus.PENDING)
    ).scalars().all()

    if not stuck_records:
        return {"swept": 0}

    # Group by user conceptually for processing
    swept_count = 0
    for record in stuck_records:
        # Wrap payload properly
        raw_payload = record.payload
        # Run it through the primary synchronized processor logic
        res = process_sync_batch(db, record.user_id, [raw_payload])
        # Note: process_sync_batch already handles clearing the queue item automatically inside `stuck_queue_item`
        swept_count += res["summary"]["synced"] + res["summary"]["duplicate"] + res["summary"]["rejected"]

    return {"swept": swept_count}

