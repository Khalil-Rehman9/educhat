from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config.settings import APP_NAME, APP_DESCRIPTION, VERSION, API_PREFIX, BACKEND_HOST, BACKEND_PORT

# Import routers
from app.backend.api.routers.documents import router as documents_router
from app.backend.api.routers.chat import router as chat_router
from app.backend.api.routers.quiz import router as quiz_router

# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=VERSION,
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router, prefix=f"{API_PREFIX}/documents", tags=["documents"])
app.include_router(chat_router, prefix=f"{API_PREFIX}/chat", tags=["chat"])
app.include_router(quiz_router, prefix=f"{API_PREFIX}/quiz", tags=["quiz"])

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "version": VERSION}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "detail": str(exc)},
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.backend.api.main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=True,
    ) 