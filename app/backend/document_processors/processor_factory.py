"""
Factory for creating document processors based on file type.
"""

import os
import sys
from typing import Optional
import mimetypes

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.backend.document_processors.base_processor import BaseDocumentProcessor
from app.backend.document_processors.pdf_processor import PDFProcessor
from app.backend.document_processors.docx_processor import DOCXProcessor
from app.backend.document_processors.pptx_processor import PPTXProcessor
from app.backend.document_processors.image_processor import ImageProcessor
# Remove the circular import from here
# from app.backend.services.document_service import update_document_status

class ProcessorFactory:
    """
    Factory for creating appropriate document processors based on file type.
    """
    
    @staticmethod
    def get_processor(file_path: str, document_id: Optional[str] = None) -> Optional[BaseDocumentProcessor]:
        """
        Get the appropriate processor for a document based on its file extension.
        
        Args:
            file_path: Path to the document file
            document_id: Unique identifier for the document
            
        Returns:
            An instance of the appropriate document processor or None if not supported
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        
        # Get file extension
        _, file_ext = os.path.splitext(file_path)
        file_ext = file_ext.lower()
        
        # Create and return the appropriate processor
        if file_ext == '.pdf':
            return PDFProcessor(file_path, document_id)
        elif file_ext == '.docx':
            return DOCXProcessor(file_path, document_id)
        elif file_ext == '.pptx':
            return PPTXProcessor(file_path, document_id)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return ImageProcessor(file_path, document_id)
        else:
            print(f"Unsupported file type: {file_ext}")
            return None
    
    @staticmethod
    def process_document(file_path: str, document_id: str) -> dict:
        """
        Process a document using the appropriate processor.
        
        Args:
            file_path: Path to the document file
            document_id: Unique identifier for the document
            
        Returns:
            Dictionary with processing results and status
        """
        # Import here to avoid circular import
        from app.backend.services.document_service import update_document_status
        
        result = {
            "success": False,
            "document_id": document_id,
            "message": "",
            "text": "",
            "metadata": {}
        }
        
        try:
            # Update document status to processing
            update_document_status(document_id, "processing")
            
            # Get processor
            processor = ProcessorFactory.get_processor(file_path, document_id)
            
            if not processor:
                update_document_status(document_id, "error")
                result["message"] = f"No suitable processor found for document: {file_path}"
                return result
            
            # Process document
            processed_data = processor.process()
            
            # Update document status to processed
            update_document_status(document_id, "processed", processed=True)
            
            # Update result
            result["success"] = True
            result["message"] = "Document processed successfully"
            result["text"] = processed_data.get("text", "")
            result["metadata"] = processed_data.get("metadata", {})
        
        except Exception as e:
            # Update document status to error
            update_document_status(document_id, "error")
            
            # Update result
            result["message"] = f"Error processing document: {str(e)}"
        
        return result 