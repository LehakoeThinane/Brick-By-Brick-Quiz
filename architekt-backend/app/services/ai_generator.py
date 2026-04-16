import os
import json
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

from app.models.enums import QuestionType, ReviewStatus, QuestionSource
from app.models.question import Question

load_dotenv()

# Schema for AI generated question
class AIGeneratedQuestion(BaseModel):
    question_text: str = Field(..., description="The text of the question")
    options: Dict[str, str] = Field(..., description="Multiple choice options. Keys should be A, B, C, D.")
    correct_answer: str = Field(..., description="The key of the correct option (e.g., 'A')")
    explanation: str = Field(..., description="Brief explanation of why the answer is correct")
    hint: Optional[str] = Field(None, description="A small hint for the user")
    difficulty: int = Field(2, ge=1, le=5, description="Difficulty level from 1 to 5")
    subcategory: str = Field(..., description="The specific topic or subcategory")

class AIGenerationBatch(BaseModel):
    questions: List[AIGeneratedQuestion]

async def generate_questions_with_ai(topic: str, count: int = 5) -> List[Dict[str, Any]]:
    """
    Generates a batch of technical questions using Google Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are a professional technical education expert. 
    Generate {count} high-quality, technically accurate multiple-choice questions about '{topic}'.
    Focus on solutions architecture, systems design, and backend engineering concepts.
    
    For each question, provide:
    1. The question text.
    2. 4 options (A, B, C, D).
    3. The correct answer (A, B, C, or D).
    4. A clear, technical explanation.
    5. A difficulty level (1-5).
    
    Questions should follow the PRD style: Scenario-based, Definition, or Trade-off assessments.
    """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AIGenerationBatch,
        ),
    )

    try:
        # The SDK handles the parsing into the response_schema
        batch_data = response.parsed
        generated_questions = []
        
        for q_data in batch_data.questions:
            # Prepare metadata
            ai_metadata = {
                "model": "gemini-1.5-flash",
                "topic": topic,
                "generated_at": str(uuid.uuid4()), # Just an ID for the batch/gen event
            }
            
            # Map Pydantic model to a dict compatible with our database Question model
            # but we return it as a list of dicts for the API to handle persistence
            generated_questions.append({
                "question_text": q_data.question_text,
                "options": q_data.options,
                "correct_answer": q_data.correct_answer,
                "explanation": q_data.explanation,
                "hint": q_data.hint,
                "difficulty": q_data.difficulty,
                "subcategory": q_data.subcategory,
                "ai_metadata": ai_metadata
            })
            
        return generated_questions
        
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        raise ValueError(f"Failed to generate structured content: {str(e)}")
