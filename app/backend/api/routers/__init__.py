"""
API routers package for FastAPI endpoints.
"""

from app.backend.api.routers.documents import router as documents_router
from app.backend.api.routers.chat import router as chat_router
from app.backend.api.routers.quiz import router as quiz_router

__all__ = [
    'documents_router',
    'chat_router',
    'quiz_router'
] 