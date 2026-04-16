import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.question import Question
from app.models.enums import ReviewStatus, QuestionSource, QuestionType

router = APIRouter()

class GenerateAIRequest(BaseModel):
    topic: str
    count: int = 5
    category_id: Optional[uuid.UUID] = None

@router.post("/ai/generate", summary="Trigger AI question generation (DRAFT only)")
async def trigger_ai_generation(
    payload: GenerateAIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates draft questions from AI. These are NOT live until approved.
    """
    try:
        # Lazy import so backend MVP can boot even if AI dependencies aren't configured.
        from app.services.ai_generator import generate_questions_with_ai

        raw_questions = await generate_questions_with_ai(payload.topic, payload.count)
        
        db_questions = []
        for q_data in raw_questions:
            new_q = Question(
                id=uuid.uuid4(),
                category_id=payload.category_id,
                subcategory=q_data["subcategory"],
                question_text=q_data["question_text"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                explanation=q_data["explanation"],
                hint=q_data["hint"],
                difficulty=q_data["difficulty"],
                question_type=QuestionType.SCENARIO, # Defaulting to Scenario
                source=QuestionSource.AI,
                review_status=ReviewStatus.DRAFT,
                ai_metadata=q_data["ai_metadata"],
                version=1
            )
            db.add(new_q)
            db_questions.append(new_q)
            
        db.commit()
        return {"message": f"Generated {len(db_questions)} draft questions", "count": len(db_questions)}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/drafts", summary="List all draft questions for review")
def list_draft_questions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    drafts = db.execute(
        select(Question).where(Question.review_status == ReviewStatus.DRAFT)
    ).scalars().all()
    return drafts

@router.post("/drafts/{question_id}/approve", summary="Approve a draft question")
def approve_question(
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    question = db.execute(
        select(Question).where(Question.id == question_id)
    ).scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    question.review_status = ReviewStatus.APPROVED
    db.commit()
    
    return {"message": "Question approved and is now live", "id": question_id}

@router.delete("/drafts/{question_id}", summary="Reject/Delete a draft question")
def delete_draft(
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    question = db.execute(
        select(Question).where(Question.id == question_id)
    ).scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.review_status != ReviewStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft questions can be deleted from here")
        
    db.delete(question)
    db.commit()
    
    return {"message": "Draft deleted", "id": question_id}
