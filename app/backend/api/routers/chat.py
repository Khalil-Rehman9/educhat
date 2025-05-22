from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import logging
import traceback

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.backend.services.chat_service import (
    create_chat_session,
    get_chat_history,
    add_chat_message,
    generate_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class SessionCreate(BaseModel):
    title: str
    document_ids: Optional[List[str]] = None

class MessageCreate(BaseModel):
    message: str
    session_id: str
    document_ids: Optional[List[str]] = None
    mode: Optional[str] = "standard"  # standard, eli5

class ChatResponse(BaseModel):
    response: str
    chat_history: List[Dict[str, Any]]
    sources: Optional[List[Dict[str, Any]]] = None

@router.post("/sessions", response_model=Dict[str, Any])
async def create_session(session: SessionCreate):
    """
    Create a new chat session.
    """
    try:
        result = create_chat_session(session.title, session.document_ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chat session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=List[Dict[str, Any]])
async def get_session_history(session_id: str):
    """
    Get chat history for a session.
    """
    try:
        history = get_chat_history(session_id)
        if history is None:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@router.post("/message", response_model=Dict[str, Any])
async def send_message(message: MessageCreate):
    """
    Send a message and get a response from the AI.
    """
    try:
        if not message.session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        if not message.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Use the provided mode or default to "standard"
        mode = message.mode or "standard"
        if mode not in ["standard", "eli5"]:
            raise HTTPException(status_code=400, detail="Invalid mode. Supported modes: standard, eli5")
        
        # Generate response
        response_data = generate_response(
            session_id=message.session_id, 
            message=message.message,
            document_ids=message.document_ids,
            mode=mode
            )
        
        if "error" in response_data:
            raise HTTPException(status_code=500, detail=response_data["error"])
        
        return {
            "response": response_data.get("response", ""),
            "chat_history": response_data.get("chat_history", []),
            "sources": response_data.get("sources", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}") 