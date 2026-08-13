import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BENCHMARK_DIR = DATA_DIR / "benchmark"
SESSIONS_DIR = DATA_DIR / "sessions"
VECTOR_STORES_DIR = DATA_DIR / "vector_stores"

# Ensure directories exist
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORES_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Default RAG Settings
DEFAULT_EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")  # gemini, openai, or local
DEFAULT_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")            # gemini or openai

# Model Mapping
EMBEDDING_MODELS = {
    "gemini": "gemini-embedding-2",
    "openai": "text-embedding-3-small",
    "local": "tf-idf"
}

LLM_MODELS = {
    "gemini": "gemini-flash-latest",
    "openai": "gpt-4o-mini"
}

# RAG Configuration
DEFAULT_CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1200))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
DEFAULT_TOP_K = int(os.getenv("TOP_K", 5))

# Scoring & Evidence Thresholds
# Scores are normalized similarity values in range [0, 1]
THRESHOLD_STRONG = 0.65
THRESHOLD_WEAK = 0.40

# LLM Pricing Details (Per 1,000,000 Tokens)
PRICING = {
    "gemini-1.5-flash": {
        "input": 0.075,      # $0.075 / 1M input tokens
        "output": 0.30,       # $0.30 / 1M output tokens
    },
    "gemini-flash-latest": {
        "input": 0.075,
        "output": 0.30,
    },
    "gpt-4o-mini": {
        "input": 0.150,      # $0.150 / 1M input tokens
        "output": 0.600,     # $0.600 / 1M output tokens
    }
}
