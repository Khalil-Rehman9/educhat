"""
Services package providing business logic and API integrations.
"""

from app.backend.services.document_service import save_document, get_document_list, get_document_by_id, delete_document, update_document_status
from app.backend.services.chat_service import create_chat_session, get_chat_history, add_chat_message, generate_response
from app.backend.services.openai_service import get_chat_completion, get_embeddings, analyze_image
from app.backend.services.embedding_service import generate_embeddings_for_document, search_in_document

__all__ = [
    'save_document',
    'get_document_list',
    'get_document_by_id',
    'delete_document',
    'update_document_status',
    'create_chat_session',
    'get_chat_history',
    'add_chat_message',
    'generate_response',
    'get_chat_completion',
    'get_embeddings',
    'analyze_image',
    'generate_embeddings_for_document',
    'search_in_document'
] 