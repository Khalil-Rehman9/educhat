"""
Image processor using OpenAI Vision API for text extraction and analysis.
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from PIL import Image

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.backend.document_processors.base_processor import BaseDocumentProcessor
from app.backend.services.openai_service import analyze_image

class ImageProcessor(BaseDocumentProcessor):
    def validate_image_format(self):
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg"]:
            raise ValueError("Invalid file extension for ImageProcessor.")
    """
    Processor for image files (PNG, JPG, JPEG) using OpenAI Vision API.
    """
    
    def extract_text(self) -> str:
        self.validate_image_format()
        """
        Extract text content from an image using OpenAI Vision API.
        
        Returns:
            The extracted text and analysis as a string
        """
        try:
            # Get basic image information
            with Image.open(self.file_path) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode
            
            # Use OpenAI Vision API to analyze the image
            prompt = "Please analyze this image and extract all the text content visible in it. If it's a whiteboard or notes, organize the content logically. If it's a diagram, describe its structure and components. If there are mathematical equations, format them clearly."
            analysis = analyze_image(self.file_path, prompt)
            
            # Save the analysis to a file
            analysis_path = os.path.join(self.output_dir, 'vision_analysis.txt')
            with open(analysis_path, 'w', encoding='utf-8') as f:
                f.write(analysis)
            
            return analysis
        
        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            print(error_msg)
            return f"ERROR: {error_msg}"
    
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from an image.
        
        Returns:
            Dictionary of metadata
        """
        metadata = {
            "file_path": self.file_path,
            "document_id": self.document_id,
            "processor": "ImageProcessor",
            "extraction_date": datetime.now().isoformat(),
            "width": None,
            "height": None,
            "format": None,
            "mode": None,
            "analysis_method": "OpenAI Vision API"
        }
        
        try:
            # Open the image to extract metadata
            with Image.open(self.file_path) as img:
                metadata["width"], metadata["height"] = img.size
                metadata["format"] = img.format
                metadata["mode"] = img.mode
                
                # Extract Exif data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = {
                        str(key): str(value)
                        for key, value in img._getexif().items()
                        if key in ExifTags.TAGS
                    }
                    metadata["exif"] = exif
        
        except Exception as e:
            metadata["error"] = str(e)
        
        return metadata
    
    def extract_content_types(self) -> Dict[str, Any]:
        """
        Identify the types of content in the image.
        
        Returns:
            Dictionary of identified content types and their confidence scores
        """
        try:
            # Use OpenAI Vision API to analyze the content types
            prompt = "What types of content does this image contain? Possible categories: handwritten notes, typed text, diagrams, charts, tables, equations, sketches, whiteboard content, slides, or other. List all that apply with brief descriptions."
            analysis = analyze_image(self.file_path, prompt)
            
            # Save the analysis to a file
            content_types_path = os.path.join(self.output_dir, 'content_types.txt')
            with open(content_types_path, 'w', encoding='utf-8') as f:
                f.write(analysis)
            
            return {"analysis": analysis, "path": content_types_path}
        
        except Exception as e:
            error_msg = f"Error analyzing content types: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
    
    def extract_educational_context(self) -> Dict[str, Any]:
        """
        Analyze the educational context of the image content.
        
        Returns:
            Dictionary containing educational context analysis
        """
        try:
            # Use OpenAI Vision API to analyze the educational context
            prompt = "Analyze this image from an educational perspective. What subject area does it cover? What level of education does it seem appropriate for? What key concepts or learning objectives does it address? Provide a brief summary suitable for study purposes."
            analysis = analyze_image(self.file_path, prompt)
            
            # Save the analysis to a file
            context_path = os.path.join(self.output_dir, 'educational_context.txt')
            with open(context_path, 'w', encoding='utf-8') as f:
                f.write(analysis)
            
            return {"analysis": analysis, "path": context_path}
        
        except Exception as e:
            error_msg = f"Error analyzing educational context: {str(e)}"
            print(error_msg)
            return {"error": error_msg} 