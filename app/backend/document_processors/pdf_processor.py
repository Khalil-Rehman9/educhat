"""
PDF document processor using PyPDF for text extraction.
"""

import os
import sys
import pypdf
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.backend.document_processors.base_processor import BaseDocumentProcessor

class PDFProcessor(BaseDocumentProcessor):
    def validate_doc_format(self):
        if not self.file_path.lower().endswith('.pdf'):
            raise ValueError("Invalid file extension for PDFProcessor.")
    """
    Processor for PDF documents using PyPDF.
    """
    
    def extract_text(self) -> str:
        self.validate_doc_format()
        """
        Extract text content from a PDF document.
        
        Returns:
            The extracted text content as a string
        """
        try:
            text_content = ""
            
            # Open the PDF file
            with open(self.file_path, 'rb') as file:
                # Create PDF reader object
                pdf_reader = pypdf.PdfReader(file)
                
                # Extract text from each page
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        text_content += page_text + "\n"
            
            return text_content.strip()
        
        except Exception as e:
            error_msg = f"Error extracting text from PDF: {str(e)}"
            print(error_msg)
            return f"ERROR: {error_msg}"
    
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from a PDF document.
        
        Returns:
            Dictionary of metadata
        """
        metadata = {
            "file_path": self.file_path,
            "document_id": self.document_id,
            "processor": "PDFProcessor",
            "extraction_date": datetime.now().isoformat(),
            "page_count": 0,
            "title": None,
            "author": None,
            "subject": None,
            "keywords": None,
            "creation_date": None,
            "modification_date": None
        }
        
        try:
            with open(self.file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # Get page count
                metadata["page_count"] = len(pdf_reader.pages)
                
                # Extract document info
                doc_info = pdf_reader.metadata
                
                if doc_info:
                    if doc_info.get('/Title'):
                        metadata["title"] = doc_info.get('/Title')
                    if doc_info.get('/Author'):
                        metadata["author"] = doc_info.get('/Author')
                    if doc_info.get('/Subject'):
                        metadata["subject"] = doc_info.get('/Subject')
                    if doc_info.get('/Keywords'):
                        metadata["keywords"] = doc_info.get('/Keywords')
                    if doc_info.get('/CreationDate'):
                        metadata["creation_date"] = doc_info.get('/CreationDate')
                    if doc_info.get('/ModDate'):
                        metadata["modification_date"] = doc_info.get('/ModDate')
        
        except Exception as e:
            metadata["error"] = str(e)
        
        return metadata
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """
        Extract tables from the PDF document.
        This is a placeholder for future implementation.
        
        Returns:
            List of dictionaries containing table data
        """
        # Note: Full table extraction would require additional libraries like tabula-py
        # For the MVP, we're just noting this as a future enhancement
        return []
    
    def extract_images(self) -> List[Dict[str, Any]]:
        """
        Extract images from the PDF document.
        This is a placeholder for future implementation.
        
        Returns:
            List of dictionaries containing image data
        """
        # Note: Image extraction would require additional processing
        # For the MVP, we're just noting this as a future enhancement
        return [] 