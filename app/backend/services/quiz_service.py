"""
Quiz generation service using RAG and Langchain.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.settings import OPENAI_API_KEY
from app.backend.services.embedding_service import get_vectorstore_for_documents, get_embedding_model
from app.backend.services.document_service import get_document_by_id, get_processed_text

# Langchain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional, Literal

# Function to create a properly configured ChatOpenAI instance
def get_chat_model(temperature=0.7, model="gpt-3.5-turbo-16k"):
    """Create a ChatOpenAI instance with the correct configuration."""
    try:
        # Set OpenAI API key explicitly
        return ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            temperature=temperature,
            model=model
        )
    except Exception as e:
        print(f"Error creating chat model: {str(e)}")
        return None

# Quiz question models
class QuizQuestion(BaseModel):
    """Quiz question model."""
    question: str = Field(description="The quiz question")
    type: str = Field(description="Type of question (multiple_choice, true_false, or short_answer)")
    options: Optional[List[str]] = Field(None, description="Options for multiple choice questions")
    answer: str = Field(description="The correct answer")
    explanation: str = Field(description="Explanation of the correct answer")

class Quiz(BaseModel):
    """Quiz model with multiple questions."""
    topic: Optional[str] = Field(None, description="Topic of the quiz")
    questions: List[QuizQuestion] = Field(description="List of quiz questions")

# Constants for quiz generation
QUIZ_DIFFICULTY_PROMPTS = {
    "easy": "Make the questions straightforward, covering basic concepts from the documents.",
    "medium": "Make the questions moderately challenging, requiring some understanding of concepts from the documents.",
    "hard": "Make the questions challenging, requiring deep understanding of concepts from the documents."
}

class QuizService:
    """Service for generating quizzes based on document content."""
    
    def __init__(self):
        """Initialize the quiz service."""
        # Initialize the LLM model using the helper function
        self.llm = get_chat_model(temperature=0.7, model="gpt-3.5-turbo-16k")
        if not self.llm:
            print("Warning: Could not initialize quiz model. Quiz generation will be unavailable.")
    
    def generate_quiz(
        self,
        document_ids: List[str],
        num_questions: int = 5,
        question_types: List[str] = ["multiple_choice", "true_false"],
        difficulty: str = "medium",
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on document content.
    
        Args:
            document_ids: List of document IDs
            num_questions: Number of questions to generate
            question_types: Types of questions to include
            difficulty: Difficulty level (easy, medium, hard)
            topic: Optional topic to focus on
        
        Returns:
            Dictionary with quiz information
        """
        if not self.llm:
            return {"error": "Quiz service not initialized correctly. The OpenAI LLM couldn't be loaded."}
    
        if not document_ids:
            return {"error": "No documents provided"}
    
        try:
            # Get document content
            document_content = ""
            document_titles = []
            
            for doc_id in document_ids:
                document = get_document_by_id(doc_id)
                if document:
                    text = get_processed_text(doc_id)
                    if text:
                        document_content += f"\n\n--- {document.get('title', 'Document')} ---\n\n"
                        document_content += text[:15000]  # Limit text to avoid token limits
                    document_titles.append(document.get('title', 'Document'))
    
            if not document_content:
                return {"error": "No valid document content found"}
            
            # Prepare the quiz generation prompt
            difficulty_prompt = QUIZ_DIFFICULTY_PROMPTS.get(difficulty, QUIZ_DIFFICULTY_PROMPTS["medium"])
            
            question_types_str = ", ".join(question_types)
            topic_str = f" about {topic}" if topic else ""
            
            system_template = f"""You are a quiz generator AI. 
Generate {num_questions} {difficulty} level questions{topic_str} based on the document content I provide.
{difficulty_prompt}

Include the following question types: {question_types_str}.

For multiple choice questions:
- Include 4 options
- Only ONE option should be correct
- Make the options plausible and relevant to the question

For true/false questions:
- The answer should be either "True" or "False"

For short answer questions:
- The answer should be concise, typically 1-3 words

Each question must include:
    1. The question text
2. Question type (multiple_choice, true_false, or short_answer)
3. Options (for multiple choice)
4. The correct answer
5. A brief explanation of why the answer is correct

All questions must be directly answerable from the document content provided.

DOCUMENT CONTENT:
{document_content}

Return the quiz in the following JSON format:
```json
{{
  "topic": "Optional topic name",
  "questions": [
    {{
      "question": "Question text",
      "type": "question_type",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "answer": "Correct answer",
      "explanation": "Explanation of the correct answer"
    }}
  ]
}}
```
"""
            
            human_template = f"Generate a {difficulty} level quiz with {num_questions} questions of types: {question_types_str}.{' The topic should be: ' + topic if topic else ''}"
            
            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_template),
                ("human", human_template),
            ])
            
            # Create the chain
            chain = prompt | self.llm | StrOutputParser()
            
            # Run the chain
            result = chain.invoke({})
            
            # Parse the JSON output
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                return {"error": "Failed to parse quiz output"}
            
            json_str = result[json_start:json_end]
            quiz_data = json.loads(json_str)
        
            # Add document info to the response
            response = {
                "topic": quiz_data.get("topic", topic),
                "questions": quiz_data.get("questions", []),
                "documents": document_titles,
                "difficulty": difficulty
            }
            
            return response
            
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            return {"error": f"Error generating quiz: {str(e)}"}

    def generate_topic_quiz(
        self,
        document_ids: List[str],
        topic: str,
        num_questions: int = 5,
        question_types: List[str] = ["multiple_choice", "true_false"],
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate a quiz for a specific topic based on document content.
    
        Args:
            document_ids: List of document IDs
            topic: Topic to focus on
            num_questions: Number of questions to generate
            question_types: Types of questions to include
            difficulty: Difficulty level (easy, medium, hard)
        
        Returns:
            Dictionary with quiz information
        """
        if not topic:
            return {"error": "No topic provided"}
        
        # Use the general quiz generation with a topic
        return self.generate_quiz(
            document_ids=document_ids,
            num_questions=num_questions,
            question_types=question_types,
            difficulty=difficulty,
            topic=topic
        )

# Create a singleton instance of QuizService
_quiz_service = QuizService()

# Standalone function wrappers
def generate_quiz(
    document_ids: List[str],
    num_questions: int = 5,
    question_types: List[str] = ["multiple_choice", "true_false"],
    difficulty: str = "medium",
    topic: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a quiz based on document content."""
    return _quiz_service.generate_quiz(
        document_ids=document_ids,
        num_questions=num_questions,
        question_types=question_types,
        difficulty=difficulty,
        topic=topic
    )

def generate_topic_quiz(
    document_ids: List[str],
    topic: str,
    num_questions: int = 5,
    question_types: List[str] = ["multiple_choice", "true_false"],
    difficulty: str = "medium"
) -> Dict[str, Any]:
    """Generate a quiz for a specific topic based on document content."""
    return _quiz_service.generate_topic_quiz(
        document_ids=document_ids,
        topic=topic,
        num_questions=num_questions,
        question_types=question_types,
        difficulty=difficulty
    ) 