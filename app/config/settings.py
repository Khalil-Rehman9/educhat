import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "app" / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

# Create directories if they don't exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EMBEDDINGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Keys and External Services
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# LLM Settings
LLM_MODEL = "gpt-4"
LLM_VISION_MODEL = "gpt-4-vision-preview"
EMBEDDING_MODEL = "text-embedding-ada-002"
MAX_TOKENS = 4096
TEMPERATURE = 0.2

# Application Settings
APP_NAME = "EduChat - AI Study Companion"
APP_DESCRIPTION = "An AI-powered tool for personalized academic support"
VERSION = "0.1.0"

# FastAPI Settings
API_PREFIX = "/api/v1"
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000")) 