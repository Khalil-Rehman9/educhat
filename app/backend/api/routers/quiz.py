"""
Quiz generation endpoints.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.backend.services.quiz_service import generate_quiz, generate_topic_quiz

router = APIRouter()

class QuizRequest(BaseModel):
    document_ids: List[str]
    num_questions: int = 5
    question_types: List[str] = ["multiple_choice", "true_false"]
    difficulty: str = "medium"
    topic: Optional[str] = None

class TopicQuizRequest(BaseModel):
    document_ids: List[str]
    topic: str
    num_questions: int = 5
    question_types: List[str] = ["multiple_choice", "true_false"]
    difficulty: str = "medium"

class QuizResponse(BaseModel):
    topic: Optional[str] = None
    questions: List[Dict[str, Any]]
    documents: List[str]
    difficulty: str

@router.post("/generate", response_model=Dict[str, Any])
async def create_quiz(quiz_request: QuizRequest):
    """
    Generate a quiz based on documents.
    """
    if not quiz_request.document_ids:
        raise HTTPException(status_code=400, detail="At least one document ID is required")
    
    # Validate question types
    valid_types = ["multiple_choice", "true_false", "short_answer"]
    for q_type in quiz_request.question_types:
        if q_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid question type: {q_type}. Valid types are: {', '.join(valid_types)}"
            )
    
    # Validate difficulty
    valid_difficulties = ["easy", "medium", "hard"]
    if quiz_request.difficulty not in valid_difficulties:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid difficulty: {quiz_request.difficulty}. Valid values are: {', '.join(valid_difficulties)}"
        )
    
    try:
        quiz_data = generate_quiz(
            document_ids=quiz_request.document_ids,
            num_questions=quiz_request.num_questions,
            question_types=quiz_request.question_types,
            difficulty=quiz_request.difficulty,
            topic=quiz_request.topic
        )
        
        if "error" in quiz_data:
            raise HTTPException(status_code=500, detail=quiz_data["error"])
        
        return quiz_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

@router.post("/generate/topic", response_model=Dict[str, Any])
async def create_topic_quiz(quiz_request: TopicQuizRequest):
    """
    Generate a quiz for a specific topic based on documents.
    """
    if not quiz_request.document_ids:
        raise HTTPException(status_code=400, detail="At least one document ID is required")
    
    if not quiz_request.topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    
    # Validate question types
    valid_types = ["multiple_choice", "true_false", "short_answer"]
    for q_type in quiz_request.question_types:
        if q_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid question type: {q_type}. Valid types are: {', '.join(valid_types)}"
            )
    
    # Validate difficulty
    valid_difficulties = ["easy", "medium", "hard"]
    if quiz_request.difficulty not in valid_difficulties:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid difficulty: {quiz_request.difficulty}. Valid values are: {', '.join(valid_difficulties)}"
        )
    
    try:
        quiz_data = generate_topic_quiz(
        document_ids=quiz_request.document_ids,
        topic=quiz_request.topic,
        num_questions=quiz_request.num_questions,
        question_types=quiz_request.question_types,
        difficulty=quiz_request.difficulty
    )
    
        if "error" in quiz_data:
            raise HTTPException(status_code=500, detail=quiz_data["error"])
        
        return quiz_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating topic quiz: {str(e)}") 