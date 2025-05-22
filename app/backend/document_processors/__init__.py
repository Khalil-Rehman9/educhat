"""
Document processors package for extracting text and information from various file types.
"""

from app.backend.document_processors.base_processor import BaseDocumentProcessor
from app.backend.document_processors.pdf_processor import PDFProcessor
from app.backend.document_processors.docx_processor import DOCXProcessor
from app.backend.document_processors.pptx_processor import PPTXProcessor
from app.backend.document_processors.image_processor import ImageProcessor
from app.backend.document_processors.processor_factory import ProcessorFactory

__all__ = [
    'BaseDocumentProcessor',
    'PDFProcessor',
    'DOCXProcessor',
    'PPTXProcessor',
    'ImageProcessor',
    'ProcessorFactory'
] 