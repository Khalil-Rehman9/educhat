"""
Refactor to a DocumentService class for better separation of concerns and
dependency injection. We will still store data in JSON for now.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import uuid

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR, EMBEDDINGS_DIR, DATA_DIR

DOCUMENTS_DB_PATH = os.path.join(DATA_DIR, "documents.json")

class DocumentService:
    """
    A class-based implementation of the document service, allowing dependency injection
    of ProcessorFactory and embedding generation logic. Data is still stored in JSON for now.
    """
    def __init__(self, processor_factory, data_dir=DATA_DIR,
                 raw_data_dir=RAW_DATA_DIR, processed_data_dir=PROCESSED_DATA_DIR,
                 embeddings_dir=EMBEDDINGS_DIR):
        self.processor_factory = processor_factory
        self.data_dir = data_dir
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        self.embeddings_dir = embeddings_dir
        self.documents_db_path = os.path.join(self.data_dir, "documents.json")

    def _load_documents(self) -> List[Dict[str, Any]]:
        """Load documents from the JSON file."""
        if not os.path.exists(self.documents_db_path):
            return []
        try:
            with open(self.documents_db_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Save documents to the JSON file."""
        with open(self.documents_db_path, 'w') as f:
            json.dump(documents, f, indent=2)

    def get_document_list(self) -> List[Dict[str, Any]]:
        """Get a list of all documents."""
        return self._load_documents()

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by its ID."""
        documents = self._load_documents()
        for doc in documents:
            if doc["id"] == doc_id:
                return doc
        return None

    def save_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save document metadata to the database.
        """
        now = datetime.now().isoformat()
        document["upload_date"] = now
        document.setdefault("status", "uploaded")
        document.setdefault("processed", False)
        document["last_modified"] = now

        documents = self._load_documents()
        documents.append(document)
        self._save_documents(documents)
        return document

    def update_document_status(self, doc_id: str, status: str, processed: bool = False) -> Optional[Dict[str, Any]]:
        """Update the status of a document."""
        documents = self._load_documents()
        for i, doc in enumerate(documents):
            if doc["id"] == doc_id:
                doc["status"] = status
                doc["processed"] = processed
                doc["last_modified"] = datetime.now().isoformat()
                documents[i] = doc
                self._save_documents(documents)
                return doc
        return None

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its associated files."""
        document = self.get_document_by_id(doc_id)
        if not document:
            return False

        documents = self._load_documents()
        documents = [doc for doc in documents if doc["id"] != doc_id]
        self._save_documents(documents)

        # Remove raw file
        raw_file_path = document.get("file_path")
        if raw_file_path and os.path.exists(raw_file_path):
            os.remove(raw_file_path)

        # Remove processed files
        processed_dir = os.path.join(self.processed_data_dir, doc_id)
        if os.path.exists(processed_dir):
            shutil.rmtree(processed_dir)

        # Remove embeddings
        embeddings_dir = os.path.join(self.embeddings_dir, doc_id)
        if os.path.exists(embeddings_dir):
            shutil.rmtree(embeddings_dir)

        return True

    def process_document(self, document_id: str, file, title: Optional[str] = None, background_tasks=None) -> Dict[str, Any]:
        """
        Process a document (save, extract text, generate embeddings).
        """
        valid_extensions = [".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg"]
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in valid_extensions:
            raise ValueError(f"Unsupported file type. Supported types: {', '.join(valid_extensions)}")

        # Save file to RAW_DATA_DIR
        safe_filename = f"{document_id}{file_ext}"
        os.makedirs(self.raw_data_dir, exist_ok=True)
        file_path = os.path.join(self.raw_data_dir, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)

        doc_meta = {
            "id": document_id,
            "title": title or file.filename,
            "original_filename": file.filename,
            "stored_filename": safe_filename,
            "file_type": file_ext.lstrip("."),
            "file_path": file_path,
            "file_size": file_size,
            "processed": False,
            "embedding_id": None
        }
        self.save_document(doc_meta)

        # Optionally process in background
        if background_tasks:
            def process_in_background(doc_id, path):
                processor = self.processor_factory.get_processor(path, doc_id)
                if processor:
                    processor.process()
                    # Generate embeddings
                    from app.backend.services.embedding_service import generate_embeddings_for_document
                    generate_embeddings_for_document(doc_id)
                    self.update_document_status(doc_id, "processed", processed=True)
                else:
                    self.update_document_status(doc_id, "error", processed=False)

            background_tasks.add_task(process_in_background, document_id, file_path)

        return doc_meta

    def get_processed_text(self, document_id: str) -> str:
        """Retrieve the processed text of a document."""
        document = self.get_document_by_id(document_id)
        if not document:
            print(f"Warning: Document with ID {document_id} not found")
            return ""

        # Check if document is processed
        if not document.get("processed", False):
            # Log warning but try to get text anyway if it exists
            print(f"Warning: Document {document_id} ({document.get('title', 'Untitled')}) is not marked as processed")

        # Build the path to the processed content file
        text_file_path = os.path.join(self.processed_data_dir, document_id, "content.txt")
        if not os.path.exists(text_file_path):
            print(f"Warning: Processed text file not found at {text_file_path}")
            return ""

        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content or len(content.strip()) < 50:
                    print(f"Warning: Document {document_id} has very little text content (only {len(content)} chars)")
                return content
        except Exception as e:
            print(f"Error reading processed text file for {document_id}: {str(e)}")
            return ""
            
    def get_documents(self) -> List[Dict[str, Any]]:
        """Get all documents (alias for get_document_list)."""
        return self.get_document_list()


# Import required dependencies for standalone functions
from app.backend.document_processors.processor_factory import ProcessorFactory

# Create a singleton instance of DocumentService
_processor_factory = ProcessorFactory()
_document_service = DocumentService(_processor_factory)

# Standalone function wrappers for backward compatibility
def save_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper for DocumentService.save_document"""
    return _document_service.save_document(document)

def get_document_list() -> List[Dict[str, Any]]:
    """Wrapper for DocumentService.get_document_list"""
    return _document_service.get_document_list()

def get_document_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    """Wrapper for DocumentService.get_document_by_id"""
    return _document_service.get_document_by_id(doc_id)

def delete_document(doc_id: str) -> bool:
    """Wrapper for DocumentService.delete_document"""
    return _document_service.delete_document(doc_id)

def update_document_status(doc_id: str, status: str, processed: bool = False) -> Optional[Dict[str, Any]]:
    """Wrapper for DocumentService.update_document_status"""
    return _document_service.update_document_status(doc_id, status, processed)

def process_document(document_id: str, file, title: Optional[str] = None, background_tasks=None) -> Dict[str, Any]:
    """Wrapper for DocumentService.process_document"""
    return _document_service.process_document(document_id, file, title, background_tasks)

def get_processed_text(document_id: str) -> str:
    """Wrapper for DocumentService.get_processed_text"""
    return _document_service.get_processed_text(document_id)

def get_documents() -> List[Dict[str, Any]]:
    """Wrapper for DocumentService.get_documents"""
    return _document_service.get_documents()