from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.core.rag import run_rag_pipeline

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class AskRequest(BaseModel):
    question: str
    mode: str  # "benchmark" or "sessions/<session_id>"
    top_k: Optional[int] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None

@router.post("/ask")
def ask_question(req: AskRequest):
    """Answers a query using the RAG pipeline in either benchmark or session mode."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    try:
        # Run RAG pipeline
        result = run_rag_pipeline(
            question=req.question,
            namespace=req.mode,
            top_k=req.top_k,
            api_key_override=req.api_key,
            provider_override=req.provider
        )
        return result
    except Exception as e:
        # Avoid leaking raw stack traces, log it and return clean error
        print(f"[ERROR] Chat API exception: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while generating the answer: {str(e)}"
        )
