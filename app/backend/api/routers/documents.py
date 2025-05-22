from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import shutil
import uuid
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.config.settings import RAW_DATA_DIR
from app.backend.services.document_service import save_document, get_document_list, get_document_by_id, delete_document, process_document, get_documents, get_processed_text
from app.backend.document_processors.processor_factory import ProcessorFactory
from app.backend.services.embedding_service import generate_embeddings_for_document
from app.backend.services.openai_service import generate_document_summary

router = APIRouter()

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    upload_date: str
    file_size: int
    status: str
    processed: bool

class Document(BaseModel):
    id: str
    title: str
    original_filename: str
    file_type: str
    upload_date: str
    processed: bool
    embedding_id: Optional[str] = None

class DocumentList(BaseModel):
    documents: List[Document]

class DocumentSummary(BaseModel):
    document_id: str
    title: str
    summary: str

def process_document_task(document_id: str, file_path: str):
    """
    Background task to process a document and generate embeddings.
    """
    # Process the document
    result = ProcessorFactory.process_document(file_path, document_id)
    
    # Generate embeddings if document was processed successfully
    if result["success"]:
        generate_embeddings_for_document(document_id)

@router.post("/upload", response_model=Document)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """
    Upload and process a new document.
    """
    # Generate a unique ID for the document
    document_id = str(uuid.uuid4())
    
    # Process the document (save, extract text, generate embeddings)
    try:
        document = process_document(document_id, file, title, background_tasks)
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/", response_model=DocumentList)
async def list_documents():
    """
    Get a list of all available documents.
    """
    documents = get_documents()
    return {"documents": documents}

@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str):
    """
    Get information about a specific document.
    """
    document = get_document_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.get("/{document_id}/summary", response_model=DocumentSummary)
async def get_document_summary(document_id: str):
    """
    Generate a summary of a specific document.
    """
    try:
        # Get document info
        document = get_document_by_id(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
        # Get the title for logging purposes
        title = document.get("title") or document.get("original_filename", "Unknown document")
    
        # Check if document is processed
        if not document.get("processed", False):
            # Don't error out, try to get text anyway
            print(f"Warning: Document {title} (ID: {document_id}) is marked as not processed but attempting to generate summary anyway")
    
        # Get the document text
        document_text = get_processed_text(document_id)
        if not document_text or len(document_text.strip()) < 50:  # Check if text is too short
            raise HTTPException(status_code=400, detail=f"Document text is empty or too short for {title}")
    
        # Generate summary
        print(f"Generating summary for document: {title} (ID: {document_id})")
        summary = generate_document_summary(document_text, title)
    
        # If the summary is an error message from the OpenAI service
        if summary.startswith("Error:") or summary.startswith("I'm having trouble"):
            print(f"Error generating summary: {summary}")
            raise HTTPException(status_code=500, detail=summary)
    
        return DocumentSummary(
            document_id=document_id,
            title=title,
            summary=summary
        )
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        print(f"Unexpected error generating summary for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating document summary: {str(e)}")

@router.delete("/{document_id}")
async def remove_document(document_id: str):
    """
    Delete a document and its processed data.
    """
    success = delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document successfully deleted"} 