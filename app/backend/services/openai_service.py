import os
import openai
from typing import List, Dict, Any, Optional
import base64
import logging
import sys
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.settings import OPENAI_API_KEY, LLM_MODEL, LLM_VISION_MODEL, EMBEDDING_MODEL, MAX_TOKENS, TEMPERATURE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up retry mechanism for API calls
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError, httpx.HTTPError, httpx.TimeoutException)),
    reraise=True
)
def api_call_with_retry(func, *args, **kwargs):
    """Execute an API call with retry logic for better reliability"""
    try:
        return func(*args, **kwargs)
    except (openai.APIError, openai.APIConnectionError, httpx.HTTPError, httpx.TimeoutException) as e:
        logger.warning(f"API call failed, retrying... Error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unrecoverable error in API call: {str(e)}")
        raise

# Initialize OpenAI client with custom timeout
try:
    # Set the API key globally
    openai.api_key = OPENAI_API_KEY
    
    # Create a custom HTTP client with longer timeouts
    http_client = httpx.Client(timeout=60.0)  # 60 second timeout
    client = openai.OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)
    logger.info("OpenAI client initialized successfully with custom HTTP client")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    # Fallback to simple client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    logger.info("Fallback to simple OpenAI client")

def get_chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    model: str = LLM_MODEL
) -> str:
    """
    Get a chat completion from OpenAI API with retry logic.
    
    Args:
        messages: List of message objects with role and content
        temperature: Controls randomness (0-2)
        max_tokens: Maximum tokens to generate
        model: Model to use
        
    Returns:
        Generated text response
    """
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
    
    try:
        def make_api_call():
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        # Make API call with retry logic
        response = api_call_with_retry(make_api_call)
        return response.choices[0].message.content or ""
    
    except Exception as e:
        error_msg = f"Error calling OpenAI API: {str(e)}"
        logger.error(error_msg)
        return f"I'm having trouble connecting to my knowledge service. Please try again later. Error details: {str(e)[:100]}..."

def get_embeddings(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """
    Get embeddings for a text string with retry logic.
    
    Args:
        text: Text to embed
        model: Embedding model to use
        
    Returns:
        Vector of embeddings
    """
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not configured")
        return []
    
    try:
        def make_api_call():
            return client.embeddings.create(
                model=model,
                input=text
            )
        
        # Make API call with retry logic
        response = api_call_with_retry(make_api_call)
        return response.data[0].embedding
    
    except Exception as e:
        logger.error(f"Error getting embeddings: {str(e)}")
        return []

def analyze_image(
    image_path: str,
    prompt: str = "Analyze this image and extract all the text and information from it.",
    model: str = LLM_VISION_MODEL
) -> str:
    """
    Analyze an image using GPT-4 Vision with retry logic.
    
    Args:
        image_path: Path to the image file
        prompt: Instruction for image analysis
        model: Vision model to use
        
    Returns:
        Analysis of the image
    """
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
    
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}"
    
    try:
        # Read the image file and convert to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        def make_api_call():
            return client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that can analyze images and extract text and information from them."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=MAX_TOKENS
            )
        
        # Make API call with retry logic
        response = api_call_with_retry(make_api_call)
        return response.choices[0].message.content or ""
    
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return f"I'm having trouble analyzing this image. Error: {str(e)}"

def generate_document_summary(document_text: str, title: str = "") -> str:
    """
    Generate a summary of the document using OpenAI.
    
    Args:
        document_text: The text content of the document
        title: The title of the document
        
    Returns:
        A summary of the document
    """
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not configured when generating document summary")
        return "Error: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
    
    # Check if document text is valid
    if not document_text or len(document_text.strip()) < 50:
        logger.error(f"Document text is too short to generate summary for {title}")
        return "Error: Document text is too short to generate a meaningful summary"
    
    # If document is very long, truncate it to avoid token limits
    max_chars = 15000  # Approximately 3000-4000 tokens
    original_length = len(document_text)
    if original_length > max_chars:
        document_text = document_text[:max_chars] + "..."
        logger.info(f"Truncated document from {original_length} to {max_chars} characters for summarization")
    
    prompt = (
        f"Please provide a comprehensive summary of the following document"
        f"{' titled: ' + title if title else ''}. "
        "Include the main points, key findings, and important details. "
        "Structure the summary in a clear, organized manner with appropriate headings."
    )
    
    try:
        logger.info(f"Generating summary for document: {title} (Length: {len(document_text)} chars)")
        
        def make_api_call():
            return client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at summarizing academic and educational content."
                    },
                    {
                        "role": "user",
                        "content": prompt + "\n\nDocument content:\n" + document_text
                    }
                ],
                temperature=0.5,  # Lower temperature for more focused summary
                max_tokens=1000   # Limit summary length
            )
        
        # Make API call with retry logic
        response = api_call_with_retry(make_api_call)
        summary = response.choices[0].message.content or ""
        
        # Log success
        logger.info(f"Successfully generated summary for {title} ({len(summary)} chars)")
        return summary
    
    except Exception as e:
        error_msg = f"Error generating document summary: {str(e)}"
        logger.error(error_msg)
        return f"I'm having trouble generating a summary for this document. Error: {str(e)}" 