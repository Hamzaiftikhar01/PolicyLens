from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from pathlib import Path
import json
import shutil
import uuid
import config
from app.core.pdf import extract_pdf_chunks
from app.core.embeddings import get_embedder
from app.core.vector_store import get_vector_store

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("/list")
def list_documents(session_id: Optional[str] = None):
    """Lists both the fixed benchmark corpus documents and temporary user-uploaded documents."""
    docs_list = []
    
    # 1. Load fixed benchmark documents
    benchmark_vs = get_vector_store("benchmark")
    is_benchmark_indexed = not benchmark_vs.is_empty
    
    meta_path = config.BENCHMARK_DIR / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r") as f:
                benchmark_docs = json.load(f)
                for doc in benchmark_docs:
                    pdf_path = config.BENCHMARK_DIR / doc["filename"]
                    pdf_exists = pdf_path.exists()
                    
                    # Compute page count dynamically using PyMuPDF if available
                    pages = "N/A"
                    if pdf_exists:
                        try:
                            import fitz
                            pdf_doc = fitz.open(pdf_path)
                            pages = len(pdf_doc)
                            pdf_doc.close()
                        except Exception:
                            pass
                            
                    # Count chunks if indexed
                    chunk_count = sum(1 for c in benchmark_vs.chunks if c["document_id"] == doc["document_id"])
                    
                    docs_list.append({
                        "document_id": doc["document_id"],
                        "title": doc["title"],
                        "category": doc["category"],
                        "version": doc.get("version", "Active"),
                        "source": doc["source"],
                        "filename": doc["filename"],
                        "type": "benchmark",
                        "status": "Indexed" if (is_benchmark_indexed and chunk_count > 0) else ("Available" if pdf_exists else "Missing"),
                        "pages": pages,
                        "chunks": chunk_count
                    })
        except Exception as e:
            print(f"[ERROR] Error loading benchmark metadata: {e}")
            
    # 2. Load session-uploaded documents
    if session_id:
        session_vs = get_vector_store(f"sessions/{session_id}")
        if not session_vs.is_empty:
            # We can group chunks in the session vector store by document_id to list the documents
            session_docs = {}
            for chunk in session_vs.chunks:
                doc_id = chunk["document_id"]
                if doc_id not in session_docs:
                    session_docs[doc_id] = {
                        "document_id": doc_id,
                        "title": chunk["document_title"],
                        "category": "User Upload",
                        "version": "Session Doc",
                        "source": "Local Upload",
                        "filename": chunk["document_title"],
                        "type": "session",
                        "status": "Indexed",
                        "pages": chunk.get("metadata", {}).get("page_end", 1),
                        "chunks": 0
                    }
                session_docs[doc_id]["chunks"] += 1
                
            docs_list.extend(list(session_docs.values()))
            
    return docs_list


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    session_id: str = Form(...),
    provider: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None)
):
    """
    Uploads and indexes custom PDFs for a specific temporary session.
    Segments structural elements and generates embeddings.
    """
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="Invalid Session ID.")
        
    session_dir = config.SESSIONS_DIR / session_id
    doc_dir = session_dir / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    
    processed_docs = []
    all_chunks = []
    
    # 1. Save and parse PDF documents
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            # Ignore non-PDF files
            continue
            
        dest_path = doc_dir / file.filename
        
        try:
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file {file.filename}: {str(e)}")
            
        doc_id = f"session_doc_{uuid.uuid4().hex[:8]}"
        doc_title = file.filename
        
        try:
            # Structurally parse the user PDF
            chunks = extract_pdf_chunks(
                pdf_path=dest_path,
                document_id=doc_id,
                document_title=doc_title,
                doc_metadata={"session_id": session_id, "type": "user_upload"},
                chunk_size=config.DEFAULT_CHUNK_SIZE,
                overlap=config.DEFAULT_CHUNK_OVERLAP
            )
            
            if chunks:
                all_chunks.extend(chunks)
                processed_docs.append({
                    "filename": file.filename,
                    "document_id": doc_id,
                    "chunks_count": len(chunks)
                })
        except Exception as e:
            # Clean up saved file on parsing error
            if dest_path.exists():
                os.remove(dest_path)
            raise HTTPException(status_code=422, detail=f"Failed to parse PDF {file.filename}: {str(e)}")
            
    if not all_chunks:
        raise HTTPException(status_code=400, detail="No readable content or text could be extracted from the uploaded files.")
        
    # 2. Get embedder and generate embeddings
    try:
        embedder = get_embedder(provider=provider, api_key=api_key)
        texts = [c["text"] for c in all_chunks]
        embeddings = embedder.embed_documents(texts)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Embedding generation failed: {str(e)}. Please check your API settings."
        )
        
    # 3. Add to Session Vector Store
    try:
        session_vs = get_vector_store(f"sessions/{session_id}")
        session_vs.add_documents(all_chunks, embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index documents: {str(e)}")
        
    return {
        "message": f"Successfully indexed {len(processed_docs)} documents.",
        "processed_documents": processed_docs,
        "total_chunks": len(all_chunks)
    }


@router.post("/clear-session")
def clear_session_index(session_id: str = Form(...)):
    """Removes all temporary files and vector indexes for a session."""
    session_dir = config.SESSIONS_DIR / session_id
    if session_dir.exists():
        try:
            shutil.rmtree(session_dir)
            return {"message": f"Session {session_id} index and files deleted."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting session directory: {str(e)}")
    return {"message": "Session already empty."}


@router.get("/download/{document_id}")
def download_benchmark_pdf(document_id: str):
    """Serves the locally stored benchmark PDF file directly."""
    meta_path = config.BENCHMARK_DIR / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark metadata catalog not found.")
        
    try:
        with open(meta_path, "r") as f:
            benchmark_docs = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse metadata: {str(e)}")
        
    doc = next((d for d in benchmark_docs if d["document_id"] == document_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document ID not found in metadata catalog.")
        
    pdf_path = config.BENCHMARK_DIR / doc["filename"]
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF file '{doc['filename']}' not found on disk.")
        
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=doc["filename"]
    )
