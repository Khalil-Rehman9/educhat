"""
Service for generating and managing vector embeddings using Langchain.
"""

import os
import sys
import json
import numpy as np
import shutil
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.settings import EMBEDDINGS_DIR, PROCESSED_DATA_DIR, DATA_DIR, OPENAI_API_KEY

# Langchain imports for RAG
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Create a properly configured OpenAIEmbeddings instance
def get_embedding_model():
    """Create an OpenAIEmbeddings instance with the correct configuration."""
    try:
        # Set OpenAI API key from environment
        return OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-ada-002"
        )
    except Exception as e:
        print(f"Error creating embedding model: {str(e)}")
        return None

class EmbeddingService:
    """
    Service for generating and managing vector embeddings using Langchain.
    """
    
    def __init__(self, document_id: str):
        """
        Initialize the embedding service for a specific document.
        
        Args:
            document_id: ID of the document to embed
        """
        self.document_id = document_id
        self.embeddings_dir = os.path.join(EMBEDDINGS_DIR, document_id)
        
        # Create embeddings directory if it doesn't exist
        os.makedirs(self.embeddings_dir, exist_ok=True)
        
        # Paths for storing index and metadata
        self.faiss_index_path = os.path.join(self.embeddings_dir, 'faiss_index')
        self.metadata_path = os.path.join(self.embeddings_dir, 'chunks_metadata.json')
        
        # Initialize OpenAI embeddings
        self.embedding_model = get_embedding_model()
    
    def generate_embeddings(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> bool:
        """
        Generate embeddings for document chunks using Langchain.
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.embedding_model:
                print("Embedding model not initialized")
                return False
                
            # Get the processed document content
            processed_dir = os.path.join(PROCESSED_DATA_DIR, self.document_id)
            content_path = os.path.join(processed_dir, 'content.txt')
            
            if not os.path.exists(content_path):
                print(f"Processed content not found for document: {self.document_id}")
                return False
            
            # Read the document content
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create chunks using Langchain's text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )
            
            # Get document metadata from metadata.json if it exists
            doc_metadata = {}
            metadata_path = os.path.join(processed_dir, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        doc_metadata = json.load(f)
                except Exception as e:
                    print(f"Error reading metadata file: {str(e)}")
            
            # Create Langchain documents with metadata
            langchain_docs = [
                Document(
                    page_content=content,
                    metadata={
                        "document_id": self.document_id,
                        "source": doc_metadata.get("title", "Unknown"),
                        "created_at": doc_metadata.get("created_at", datetime.now().isoformat()),
                        **doc_metadata
                    }
                )
            ]
            
            # Split documents into chunks
            chunks = text_splitter.split_documents(langchain_docs)
            
            if not chunks:
                print(f"No chunks generated for document: {self.document_id}")
                return False
            
            # Generate embeddings and create FAISS index
            vectorstore = FAISS.from_documents(chunks, self.embedding_model)
            
            # Save FAISS index
            vectorstore.save_local(self.faiss_index_path)
            
            # Save chunks metadata for reference
            chunks_metadata = []
            for i, chunk in enumerate(chunks):
                    chunks_metadata.append({
                        "chunk_id": i,
                        "document_id": self.document_id,
                    "text": chunk.page_content[:100] + "..." if len(chunk.page_content) > 100 else chunk.page_content,
                    "metadata": chunk.metadata
                })
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(chunks_metadata, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return False
    
    def has_embeddings(self) -> bool:
        """
        Check if embeddings exist for the document.
        
        Returns:
            True if embeddings exist, False otherwise
        """
        return os.path.exists(self.faiss_index_path)
    
    def get_vectorstore(self):
        """
        Load the vector store for the document.
        
        Returns:
            FAISS vector store if it exists, None otherwise
        """
        if not self.has_embeddings():
            return None
            
        try:
            return FAISS.load_local(self.faiss_index_path, self.embedding_model)
        except Exception as e:
            print(f"Error loading vector store: {str(e)}")
            return None
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for the most relevant document chunks for a query.
        
        Args:
            query: Query string
            top_k: Number of top results to return
            
        Returns:
            List of the top_k most similar chunks with their metadata
        """
        try:
            vectorstore = self.get_vectorstore()
            if not vectorstore:
                return []
            
            # Search for similar chunks
            search_results = vectorstore.similarity_search_with_score(query, k=top_k)
            
            # Format results
            results = []
            for doc, score in search_results:
                results.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(1.0 / (1.0 + score))  # Convert distance to similarity
                })
            
            return results
        
        except Exception as e:
            print(f"Error searching embeddings: {str(e)}")
            return []


def generate_embeddings_for_document(document_id: str) -> bool:
    """
    Generate embeddings for a document.
    
    Args:
        document_id: ID of the document
        
    Returns:
        True if successful, False otherwise
    """
    embedding_service = EmbeddingService(document_id)
    return embedding_service.generate_embeddings()


def search_in_document(document_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for relevant content in a document.
    
    Args:
        document_id: ID of the document
        query: Search query
        top_k: Number of top results to return
        
    Returns:
        List of the top_k most similar chunks with their metadata
    """
    embedding_service = EmbeddingService(document_id)
    
    # Generate embeddings if they don't exist
    if not embedding_service.has_embeddings():
        if not embedding_service.generate_embeddings():
            return []
    
    return embedding_service.search(query, top_k) 


def get_vectorstore_for_documents(document_ids: List[str]):
    """
    Get a combined vector store for multiple documents.
    
    Args:
        document_ids: List of document IDs
        
    Returns:
        FAISS vector store with all documents
    """
    if not document_ids:
        print("No document IDs provided for vectorstore creation")
        return None
        
    try:
        # Get embedding model using our helper function
        embedding_model = get_embedding_model()
        if not embedding_model:
            print("Failed to initialize embedding model for combined vectorstore")
            return None
            
        combined_docs = []
        missing_embeddings = []
        
        # Get individual vector stores
        for doc_id in document_ids:
            embedding_service = EmbeddingService(doc_id)
            
            # Check if document has embeddings, generate them if not
            if not embedding_service.has_embeddings():
                print(f"Embeddings not found for document {doc_id}, generating now...")
                success = embedding_service.generate_embeddings()
                if not success:
                    print(f"Failed to generate embeddings for document {doc_id}")
                    missing_embeddings.append(doc_id)
                    continue
            
            # Now try to get the vectorstore
            vectorstore = embedding_service.get_vectorstore()
            
            if vectorstore:
                # Get the documents from the vector store
                try:
                    faiss_docs = vectorstore.similarity_search("", k=1000)  # Get all docs
                    combined_docs.extend(faiss_docs)
                    print(f"Added {len(faiss_docs)} chunks from document {doc_id}")
                except Exception as e:
                    print(f"Error retrieving documents from vectorstore for {doc_id}: {str(e)}")
            else:
                print(f"Failed to get vectorstore for document {doc_id}")
                missing_embeddings.append(doc_id)
        
        if missing_embeddings:
            print(f"Warning: Could not get embeddings for documents: {', '.join(missing_embeddings)}")
        
        if not combined_docs:
            print("No document chunks found for any of the requested documents")
            return None
            
        # Create a new vector store with all documents
        print(f"Creating combined vectorstore with {len(combined_docs)} chunks from {len(document_ids) - len(missing_embeddings)} documents")
        return FAISS.from_documents(combined_docs, embedding_model)
    
    except Exception as e:
        print(f"Error creating combined vector store: {str(e)}")
        return None 