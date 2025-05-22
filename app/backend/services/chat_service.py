"""
Chat service for managing conversations with RAG using Langchain.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.settings import DATA_DIR, OPENAI_API_KEY
from app.backend.services.embedding_service import get_vectorstore_for_documents, search_in_document, get_embedding_model
from app.backend.services.document_service import get_document_by_id, get_processed_text

# Langchain imports for RAG
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.conversational_retrieval.base import BaseConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# Directory for storing chat sessions
CHAT_SESSIONS_DIR = os.path.join(DATA_DIR, "chat_sessions")
os.makedirs(CHAT_SESSIONS_DIR, exist_ok=True)

# Function to create a properly configured ChatOpenAI instance
def get_chat_model(temperature=0.7, model="gpt-3.5-turbo"):
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

# Templates for chat prompts
STANDARD_SYSTEM_TEMPLATE = """You are an AI assistant helping with document-based questions.
Use the following pieces of retrieved context to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Retrieved context:
{context}

Chat History:
{chat_history}

User: {question}
AI Assistant:"""

ELI5_SYSTEM_TEMPLATE = """You are an AI assistant helping explain complex topics in simple terms.
Use the following pieces of retrieved context to answer the user's question.
Explain like you would to a 5-year-old using simple language, helpful analogies, and clear examples.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Retrieved context:
{context}

Chat History:
{chat_history}

User: {question}
AI Assistant:"""

class ChatService:
    """Service for managing chat sessions and generating responses using RAG."""
    
    def __init__(self):
        """Initialize the chat service."""
        # Always initialize the chat_chains attribute
        self.chat_chains = {}
        
        # Initialize the LLM model using the helper function
        self.llm = get_chat_model(temperature=0.7, model="gpt-3.5-turbo")
        if not self.llm:
            print("Warning: Could not initialize chat model. Chat functionality will be limited.")

    def create_session(self, title: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new chat session.
            
        Args:
            title: Title of the chat session
            document_ids: List of document IDs to associate with the session
                
        Returns:
            Dictionary with session information
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            "id": session_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "document_ids": document_ids or [],
            "messages": []
        }
            
        # Save session data
        session_file = os.path.join(CHAT_SESSIONS_DIR, f"{session_id}.json")
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return session_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get chat session information.
            
        Args:
            session_id: ID of the chat session
                
        Returns:
            Dictionary with session information or None if not found
        """
        session_file = os.path.join(CHAT_SESSIONS_DIR, f"{session_id}.json")
            
        if not os.path.exists(session_file):
            return None
            
        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat session: {str(e)}")
        return None

    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get chat history for a session.
            
        Args:
            session_id: ID of the chat session
                
        Returns:
            List of chat messages
        """
        session_data = self.get_session(session_id)
            
        if not session_data:
            return []
        
        return session_data.get("messages", [])

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to the chat history.
            
        Args:
            session_id: ID of the chat session
            role: Role of the message sender (user or assistant)
            content: Content of the message
                
        Returns:
            True if successful, False otherwise
        """
        session_data = self.get_session(session_id)
            
        if not session_data:
            return False
            
        # Add message
        session_data["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
            
        # Save session data
        session_file = os.path.join(CHAT_SESSIONS_DIR, f"{session_id}.json")
        try:
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving chat message: {str(e)}")
            return False
        
    def _get_chat_chain(self, session_id: str, document_ids: List[str], mode: str = "standard") -> Optional[BaseConversationalRetrievalChain]:
        """
        Get or create a chat chain for a session.
            
        Args:
            session_id: ID of the chat session
            document_ids: List of document IDs
            mode: Chat mode (standard or eli5)
                
        Returns:
            Conversational retrieval chain or None if creation fails
        """
        # Check if chain already exists in cache
        cache_key = f"{session_id}_{'-'.join(sorted(document_ids))}_{mode}"
        if cache_key in self.chat_chains:
            print(f"Using cached chat chain for session {session_id}")
            return self.chat_chains[cache_key]
            
        if not self.llm:
            print("LLM not initialized in chat service")
            return None
        
        if not document_ids:
            print("No document IDs provided for chat session")
            return None
            
        try:
            # Verify documents exist
            from app.backend.services.document_service import get_document_by_id
            
            valid_docs = []
            for doc_id in document_ids:
                doc = get_document_by_id(doc_id)
                if doc:
                    valid_docs.append(doc_id)
                    print(f"Document {doc_id} ({doc.get('title', 'Untitled')}) is valid")
                else:
                    print(f"Document {doc_id} not found in database")
            
            if not valid_docs:
                print("None of the requested documents exist in the database")
                return None
                
            # Get vector store for the documents
            print(f"Getting vectorstore for documents: {', '.join(valid_docs)}")
            vectorstore = get_vectorstore_for_documents(valid_docs)
                
            if not vectorstore:
                print(f"Failed to create vectorstore for documents: {', '.join(valid_docs)}")
                return None
                
            # Create memory for conversation history
            memory = ConversationBufferMemory(
                memory_key="chat_history", 
                return_messages=True,
                output_key="answer"
            )
                
            # Select prompt template based on mode
            if mode == "eli5":
                template = ELI5_SYSTEM_TEMPLATE
            else:  # standard
                template = STANDARD_SYSTEM_TEMPLATE
                    
            prompt = PromptTemplate(
                template=template,
                input_variables=["context", "chat_history", "question"]
            )
                
            # Create the chain
            print(f"Creating ConversationalRetrievalChain for session {session_id}")
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
                memory=memory,
                combine_docs_chain_kwargs={"prompt": prompt},
                return_source_documents=True,
                verbose=True
            )
                
            # Cache the chain
            self.chat_chains[cache_key] = chain
            print(f"Successfully created chat chain for session {session_id}")
                
            return chain
            
        except Exception as e:
            print(f"Error creating chat chain: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
    def generate_response(self, session_id: str, message: str, document_ids: Optional[List[str]] = None, mode: str = "standard") -> Dict[str, Any]:
        """
        Generate a response to a message using RAG.
        
        Args:
            session_id: ID of the chat session
            message: User message
            document_ids: List of document IDs (optional, will use session documents if not provided)
            mode: Chat mode (standard or eli5)
            
        Returns:
            Dictionary with response information
        """
        # Get session data
        session_data = self.get_session(session_id)
        
        if not session_data:
            return {"error": "Chat session not found"}
        
        # Use provided document IDs or session document IDs
        doc_ids = document_ids or session_data.get("document_ids", [])
        
        # Add user message to history
        self.add_message(session_id, "user", message)
        
        try:
            # Check if documents are provided
            if not doc_ids:
                # Generate a direct response using just the model without RAG
                response = "I don't have any documents to reference. Please select one or more documents to discuss, or ask me a general question."
                self.add_message(session_id, "assistant", response)
                return {
                    "response": response,
                    "chat_history": self.get_session_history(session_id),
                    "sources": []
                }
            
            # Before getting the chat chain, try to ensure all documents are processed
            from app.backend.services.document_service import get_document_by_id, update_document_status
            from app.backend.services.embedding_service import generate_embeddings_for_document
            
            # Try to process any unprocessed documents
            for doc_id in doc_ids:
                doc = get_document_by_id(doc_id)
                if doc and not doc.get("processed", False):
                    print(f"Document {doc_id} ({doc.get('title', 'Untitled')}) is not processed, trying to process it now...")
                    # Generate embeddings (which will also process the document if needed)
                    success = generate_embeddings_for_document(doc_id)
                    if success:
                        # Update document status to processed
                        update_document_status(doc_id, "processed", processed=True)
                        print(f"Successfully processed document {doc_id}")
            
            # Get chat chain
            chain = self._get_chat_chain(session_id, doc_ids, mode)
            
            if not chain:
                # Fallback to direct completion if chain creation fails
                from app.backend.services.document_service import get_document_by_id
                
                # Check if documents exist and are processed
                invalid_docs = []
                for doc_id in doc_ids:
                    doc = get_document_by_id(doc_id)
                    if not doc:
                        invalid_docs.append(f"Document with ID {doc_id} not found")
                    elif not doc.get("processed", False):
                        invalid_docs.append(f"Document '{doc.get('title', 'Untitled')}' is not fully processed yet")
                
                if invalid_docs:
                    error_details = ". ".join(invalid_docs)
                    response = f"I'm sorry, I couldn't access the documents due to the following issues: {error_details}. Please try again later or select different documents."
                else:
                    response = "I'm sorry, I couldn't access the documents. This could be due to processing issues or missing embeddings. Please try again later or select different documents."
                
                self.add_message(session_id, "assistant", response)
                
                return {
                    "response": response,
                    "chat_history": self.get_session_history(session_id),
                    "sources": []
                }
            
            # Generate response with RAG
            chain_response = chain({"question": message})
            
            response = chain_response.get("answer", "I'm sorry, I couldn't generate a response.")
            source_documents = chain_response.get("source_documents", [])
    
            # Extract sources
            sources = []
            for doc in source_documents:
                sources.append({
                    "document_id": doc.metadata.get("document_id", ""),
                    "source": doc.metadata.get("source", "Unknown"),
                    "text": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
    
            # Add assistant message to history
            self.add_message(session_id, "assistant", response)
            
            return {
                "response": response,
                "chat_history": self.get_session_history(session_id),
                "sources": sources
            }
        
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Add error message to history
            error_response = "I'm sorry, I encountered an error while processing your request. Please try again or select different documents."
            self.add_message(session_id, "assistant", error_response)
            
            return {
                "response": error_response,
                "chat_history": self.get_session_history(session_id),
                "sources": []
            }


# Create a singleton instance of ChatService
_chat_service = ChatService()

# Standalone function wrappers
def create_chat_session(title: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a new chat session."""
    return _chat_service.create_session(title, document_ids)

def get_chat_history(session_id: str) -> List[Dict[str, str]]:
    """Get chat history for a session."""
    return _chat_service.get_session_history(session_id)

def add_chat_message(session_id: str, role: str, content: str) -> bool:
    """Add a message to the chat history."""
    return _chat_service.add_message(session_id, role, content)

def generate_response(session_id: str, message: str, document_ids: Optional[List[str]] = None, mode: str = "standard") -> Dict[str, Any]:
    """Generate a response to a message."""
    return _chat_service.generate_response(session_id, message, document_ids, mode) 