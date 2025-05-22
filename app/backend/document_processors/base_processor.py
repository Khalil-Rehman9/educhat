"""
Base document processor that defines the interface for all document processors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.settings import PROCESSED_DATA_DIR

class BaseDocumentProcessor(ABC):
    """Base abstract class for document processors."""
    
    def __init__(self, file_path: str, document_id: str):
        """
        Initialize the document processor.
        
        Args:
            file_path: Path to the document file
            document_id: Unique identifier for the document
        """
        self.file_path = file_path
        self.document_id = document_id
        self.output_dir = os.path.join(PROCESSED_DATA_DIR, document_id)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Validate the file
        self.validate_file()
    
    @abstractmethod
    def extract_text(self) -> str:
        """
        Extract text content from the document.
        
        Returns:
            The extracted text content as a string
        """
        pass
    
    @abstractmethod
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from the document.
        
        Returns:
            Dictionary of metadata
        """
        pass
    
    def process(self) -> Dict[str, Any]:
        """
        Process the document and extract text and metadata.
        
        Returns:
            Dictionary with text content and metadata
        """
        text = self.extract_text()
        metadata = self.extract_metadata()
        
        # Save processed text to output file
        text_output_path = os.path.join(self.output_dir, 'content.txt')
        with open(text_output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Save metadata to output file
        import json
        metadata_output_path = os.path.join(self.output_dir, 'metadata.json')
        with open(metadata_output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'text': text,
            'metadata': metadata,
            'text_path': text_output_path,
            'metadata_path': metadata_output_path
        }
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into chunks with specified size and overlap.
        
        Args:
            text: Text to be chunked
            chunk_size: Maximum size of each chunk in characters
            overlap: Overlap size between chunks in characters
            
        Returns:
            List of text chunks
        """
        chunks = []
        if not text:
            return chunks
        
        # Simple chunking by characters
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to end at a sentence or paragraph boundary if possible
            if end < len(text):
                # Look for paragraph break
                paragraph_end = text.rfind('\n\n', start, end)
                if paragraph_end > start + chunk_size // 2:
                    end = paragraph_end + 2
                else:
                    # Look for sentence break (period followed by space)
                    sentence_end = text.rfind('. ', start, end)
                    if sentence_end > start + chunk_size // 2:
                        end = sentence_end + 2
            
            # Add the chunk
            chunks.append(text[start:end])
            
            # Move start position with overlap
            start = end - overlap
        
        return chunks

    def validate_file(self):
        if not os.path.isfile(self.file_path):
            raise ValueError(f"File not found: {self.file_path}")
        if os.path.getsize(self.file_path) == 0:
            raise ValueError(f"File is empty: {self.file_path}")