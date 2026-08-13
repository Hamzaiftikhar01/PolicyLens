import os
import faiss
import numpy as np
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
import config

class VectorStore:
    """
    FAISS-based vector database wrapper with metadata support.
    Supports index creation, retrieval, and disk serialization.
    """
    def __init__(self, index_dir: Path, dimension: int = 768):
        self.index_dir = Path(index_dir)
        self.dimension = dimension
        self.index_path = self.index_dir / "index.faiss"
        self.metadata_path = self.index_dir / "metadata.pkl"
        
        self.index = None
        self.chunks: List[Dict[str, Any]] = []
        
        # Load index if it exists on disk
        if self.index_path.exists() and self.metadata_path.exists():
            self.load()
            
    def load(self):
        """Loads FAISS index and metadata from disk."""
        try:
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, "rb") as f:
                self.chunks = pickle.load(f)
            self.dimension = self.index.d
        except Exception as e:
            # Silently handle/log loading failure
            self.index = None
            self.chunks = []
            
    def save(self):
        """Saves FAISS index and metadata to disk."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.chunks, f)
                
    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Adds document chunks and their precomputed embeddings to the index."""
        if not chunks or not embeddings:
            return
            
        embeddings_np = np.array(embeddings, dtype=np.float32)
        
        if self.index is None:
            self.dimension = embeddings_np.shape[1]
            # Use IndexFlatIP for cosine similarity on L2-normalized vectors
            self.index = faiss.IndexFlatIP(self.dimension)
            
        # Add to FAISS index
        self.index.add(embeddings_np)
        
        # Add metadata chunks
        self.chunks.extend(chunks)
        self.save()
        
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Searches for the top-k most similar chunks.
        Returns a list of tuples containing the chunk metadata and similarity score.
        """
        if self.index is None or not self.chunks:
            return []
            
        query_np = np.array([query_embedding], dtype=np.float32)
        top_k = min(top_k, len(self.chunks))
        
        # Search the index
        scores, indices = self.index.search(query_np, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.chunks):
                continue
            
            # FAISS IndexFlatIP returns dot product. Since vectors are L2 normalized,
            # this is exactly Cosine Similarity.
            similarity_score = float(score)
            
            # Map similarity scores to a robust 0-1 scale
            similarity_score = max(0.0, min(1.0, similarity_score))
            
            results.append((self.chunks[idx], similarity_score))
            
        return results

    def clear(self):
        """Clears index and metadata, and removes files from disk."""
        self.index = None
        self.chunks = []
        if self.index_path.exists():
            os.remove(self.index_path)
        if self.metadata_path.exists():
            os.remove(self.metadata_path)
            
    @property
    def is_empty(self) -> bool:
        return self.index is None or len(self.chunks) == 0


def get_vector_store(namespace: str, dimension: int = 768) -> VectorStore:
    """
    Factory function to get a VectorStore instance for a specific namespace.
    Benchmark namespaces: "benchmark"
    Session namespaces: "sessions/<session_id>"
    """
    if namespace == "benchmark":
        index_dir = config.VECTOR_STORES_DIR / "benchmark"
    else:
        # Keep session namespace directories isolated
        session_id = namespace.replace("sessions/", "")
        index_dir = config.SESSIONS_DIR / session_id / "vector_store"
        
    return VectorStore(index_dir, dimension=dimension)
