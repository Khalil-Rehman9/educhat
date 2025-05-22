from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends, Cookie, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import requests
import os
import sys
import json
from datetime import datetime
import time
from pathlib import Path

# Fix the Python path to ensure 'app' module can be found
current_file_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_path, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import from app
from app.config.settings import APP_NAME, APP_DESCRIPTION, BACKEND_HOST, BACKEND_PORT, API_PREFIX

# API URL configuration
API_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}{API_PREFIX}"

# Create FastAPI app
app = FastAPI(title=APP_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Helper functions
def get_documents():
    """Fetch documents list from the API"""
    try:
        response = requests.get(f"{API_URL}/documents/")
        if response.status_code == 200:
            docs = response.json().get("documents", [])
            # Extract unique categories if they exist
            categories = set()
            for doc in docs:
                if "category" in doc and doc["category"]:
                    categories.add(doc["category"])
            return docs, sorted(list(categories))
        else:
            print(f"Error fetching documents: {response.text}")
            return [], []
    except Exception as e:
        print(f"Error connecting to backend: {str(e)}")
        return [], []

def create_new_session(document_ids=None):
    """Create a new chat session"""
    try:
        title = f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        response = requests.post(
            f"{API_URL}/chat/sessions",
            json={"title": title, "document_ids": document_ids or []}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error creating chat session: {response.text}")
            return None
    except Exception as e:
        print(f"Error connecting to backend: {str(e)}")
        return None

def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        response = requests.get(f"{API_URL}/chat/sessions/{session_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching chat history: {response.text}")
            return []
    except Exception as e:
        print(f"Error connecting to backend: {str(e)}")
        return []

def get_document_summary(document_id):
    """Get a summary of a document."""
    url = f"{API_URL}/documents/{document_id}/summary"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error generating document summary: {str(e)}")
        return None

def delete_document(document_id):
    """Delete a document from the backend"""
    try:
        response = requests.delete(f"{API_URL}/documents/{document_id}")
        if response.status_code == 200:
            return True
        else:
            print(f"Error deleting document: {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to backend: {str(e)}")
        return False

# Template filters
def format_datetime(value):
    """Format datetime for display"""
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        return value
    except:
        return value

# Add filters to Jinja2 templates
templates.env.filters["datetime"] = format_datetime

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, selected_docs: Optional[str] = Query(None)):
    """Main chat page"""
    # Get documents for sidebar
    documents, _ = get_documents()
    
    # Initialize variables
    selected_documents = []
    chat_history = []
    session_id = None
    chat_mode = "standard"
    
    # Get selected documents from query params
    selected_doc_ids = []
    if selected_docs:
        try:
            selected_doc_ids = json.loads(selected_docs)
        except:
            selected_doc_ids = selected_docs.split(',') if selected_docs else []
    
    # Filter selected documents
    if selected_doc_ids:
        selected_documents = [doc for doc in documents if doc.get("id") in selected_doc_ids]
    
    # Create a session if there are selected documents but no session
    if selected_documents and not session_id:
        session = create_new_session([doc.get("id") for doc in selected_documents])
        if session:
            session_id = session.get("id")
    
    # Get chat history if session exists
    if session_id:
        chat_history = get_chat_history(session_id)
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "app_name": APP_NAME,
            "app_description": APP_DESCRIPTION,
            "documents": documents,
            "selected_documents": selected_documents,
            "chat_history": chat_history,
            "session_id": session_id,
            "chat_mode": chat_mode,
            "active_tab": "chat"
        }
    )

@app.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request, selected_docs: Optional[str] = Query(None)):
    """Documents management page"""
    # Get documents and categories
    documents, categories = get_documents()
    
    # Get selected documents from query params
    selected_doc_ids = []
    if selected_docs:
        try:
            selected_doc_ids = json.loads(selected_docs)
        except:
            selected_doc_ids = selected_docs.split(',') if selected_docs else []
    
    # Count document types
    document_types = {}
    for doc in documents:
        file_type = doc.get('file_type', '').lower()
        if file_type:
            document_types[file_type] = document_types.get(file_type, 0) + 1
    
    return templates.TemplateResponse(
        "documents.html", 
        {
            "request": request, 
            "app_name": APP_NAME,
            "app_description": APP_DESCRIPTION,
            "documents": documents,
            "categories": categories,
            "document_types": document_types,
            "selected_documents": selected_doc_ids,
            "active_tab": "documents"
        }
    )

@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request, selected_docs: Optional[str] = Query(None)):
    """Quiz generation page"""
    # Get documents
    documents, _ = get_documents()
    
    # Get selected documents from query params
    selected_doc_ids = []
    if selected_docs:
        try:
            selected_doc_ids = json.loads(selected_docs)
        except:
            selected_doc_ids = selected_docs.split(',') if selected_docs else []
    
    # Filter selected documents
    selected_documents = [doc for doc in documents if doc.get("id") in selected_doc_ids]
    
    return templates.TemplateResponse(
        "quiz.html", 
        {
            "request": request, 
            "app_name": APP_NAME,
            "app_description": APP_DESCRIPTION,
            "documents": documents,
            "selected_documents": selected_documents,
            "quiz_data": None,
            "active_tab": "quiz"
        }
    )

# API Routes - These proxy requests to the backend API

@app.post("/api/chat/message")
async def send_message(message: Dict[str, Any]):
    """Send a message to the AI and get a response"""
    try:
        response = requests.post(
            f"{API_URL}/chat/message",
            json=message
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/sessions")
async def create_session(session_data: Dict[str, Any]):
    """Create a new chat session"""
    try:
        response = requests.post(
            f"{API_URL}/chat/sessions",
            json=session_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """Get chat history for a session"""
    try:
        response = requests.get(f"{API_URL}/chat/sessions/{session_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/")
async def list_documents():
    """Get a list of all documents"""
    try:
        response = requests.get(f"{API_URL}/documents/")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), title: Optional[str] = Form(None), category: Optional[str] = Form(None)):
    """Upload a document to the backend"""
    try:
        files = {"file": (file.filename, file.file, file.content_type)}
        data = {}
        
        if title:
            data["title"] = title
        
        if category:
            data["category"] = category
        
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    """Get information about a specific document"""
    try:
        response = requests.get(f"{API_URL}/documents/{document_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}/summary")
async def get_document_summary_api(document_id: str):
    """Generate a summary of a specific document"""
    try:
        response = requests.get(f"{API_URL}/documents/{document_id}/summary")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{document_id}")
async def delete_document_api(document_id: str):
    """Delete a document"""
    try:
        response = requests.delete(f"{API_URL}/documents/{document_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quiz/generate")
async def generate_quiz(quiz_request: Dict[str, Any]):
    """Generate a quiz based on documents"""
    try:
        response = requests.post(
            f"{API_URL}/quiz/generate",
            json=quiz_request
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quiz/generate/topic")
async def generate_topic_quiz(quiz_request: Dict[str, Any]):
    """Generate a topic-specific quiz based on documents"""
    try:
        response = requests.post(
            f"{API_URL}/quiz/generate/topic",
            json=quiz_request
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8501, reload=True) 