import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import config

# Initialize FastAPI App
app = FastAPI(
    title="PolicyLens API",
    description="Evidence-Grounded Pakistan & Document Intelligence",
    version="1.0.0"
)

# Import and include routers
from app.ui.dashboard import router as dashboard_router
from app.ui.chat import router as chat_router
from app.ui.documents import router as documents_router
from app.ui.evaluation import router as evaluation_router

app.include_router(dashboard_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(evaluation_router)

# Settings Models
class SettingsUpdate(BaseModel):
    embedding_provider: str
    llm_provider: str
    gemini_api_key: str
    openai_api_key: str
    chunk_size: int
    chunk_overlap: int

@app.get("/api/settings")
def get_settings():
    """Returns the current RAG and API configurations (with obfuscated keys)."""
    return {
        "embedding_provider": config.DEFAULT_EMBEDDING_PROVIDER,
        "llm_provider": config.DEFAULT_LLM_PROVIDER,
        "gemini_api_key_set": bool(config.GEMINI_API_KEY),
        "openai_api_key_set": bool(config.OPENAI_API_KEY),
        "chunk_size": config.DEFAULT_CHUNK_SIZE,
        "chunk_overlap": config.DEFAULT_CHUNK_OVERLAP,
        "models": {
            "embedding": config.EMBEDDING_MODELS.get(config.DEFAULT_EMBEDDING_PROVIDER, "local"),
            "llm": config.LLM_MODELS.get(config.DEFAULT_LLM_PROVIDER, "local")
        }
    }

@app.post("/api/settings")
def update_settings(settings: SettingsUpdate):
    """Updates RAG parameters and API credentials in memory."""
    emb_p = settings.embedding_provider.lower()
    llm_p = settings.llm_provider.lower()
    
    if emb_p not in ["gemini", "openai", "local"]:
        raise HTTPException(status_code=400, detail="Invalid embedding provider.")
    if llm_p not in ["gemini", "openai"]:
        raise HTTPException(status_code=400, detail="Invalid LLM provider.")
        
    config.DEFAULT_EMBEDDING_PROVIDER = emb_p
    config.DEFAULT_LLM_PROVIDER = llm_p
    config.DEFAULT_CHUNK_SIZE = settings.chunk_size
    config.DEFAULT_CHUNK_OVERLAP = settings.chunk_overlap
    
    if settings.gemini_api_key.strip():
        config.GEMINI_API_KEY = settings.gemini_api_key.strip()
    if settings.openai_api_key.strip():
        config.OPENAI_API_KEY = settings.openai_api_key.strip()
        
    # Attempt to persist back to .env
    env_path = config.BASE_DIR / ".env"
    try:
        with open(env_path, "w") as f:
            f.write("# Auto-generated and updated by PolicyLens\n")
            f.write(f"GEMINI_API_KEY={config.GEMINI_API_KEY}\n")
            f.write(f"OPENAI_API_KEY={config.OPENAI_API_KEY}\n")
            f.write(f"EMBEDDING_PROVIDER={config.DEFAULT_EMBEDDING_PROVIDER}\n")
            f.write(f"LLM_PROVIDER={config.DEFAULT_LLM_PROVIDER}\n")
            f.write(f"CHUNK_SIZE={config.DEFAULT_CHUNK_SIZE}\n")
            f.write(f"CHUNK_OVERLAP={config.DEFAULT_CHUNK_OVERLAP}\n")
    except Exception as e:
        print(f"[WARNING] Could not write changes to .env file: {e}")
        
    return {"message": "Settings updated successfully."}


# Mount Static Files and Root Route
static_dir = config.BASE_DIR / "app" / "ui" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def get_index():
    """Serves the main SPA index.html."""
    index_path = static_dir / "index.html"
    return FileResponse(str(index_path))
