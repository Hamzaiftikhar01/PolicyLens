import numpy as np
import hashlib
import requests
import time
from typing import List
import config

class BaseEmbedder:
    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class GeminiEmbedder(BaseEmbedder):
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Gemini API key is required for Gemini embeddings.")

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        model_name = config.EMBEDDING_MODELS.get("gemini", "gemini-embedding-2")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:batchEmbedContents?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        # Batch size limit for Gemini is 100
        batch_size = 100
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i+batch_size]
            requests_list = [
                {
                    "model": f"models/{model_name}", 
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": 768
                } for t in chunk
            ]
            data = {"requests": requests_list}
            
            # Simple retry logic for reliability
            for attempt in range(3):
                try:
                    response = requests.post(url, headers=headers, json=data, timeout=15)
                    response.raise_for_status()
                    res_json = response.json()
                    chunk_embeddings = [e["values"] for e in res_json["embeddings"]]
                    embeddings.extend(chunk_embeddings)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise RuntimeError(f"Gemini Embedding API failed: {e}")
                    time.sleep(2 ** attempt)
                    
        return embeddings


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required for OpenAI embeddings.")

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Batch size limit for OpenAI is typically 2048
        batch_size = 250
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i+batch_size]
            data = {
                "model": "text-embedding-3-small",
                "input": chunk
            }
            
            for attempt in range(3):
                try:
                    response = requests.post(url, headers=headers, json=data, timeout=15)
                    response.raise_for_status()
                    res_json = response.json()
                    chunk_embeddings = [item["embedding"] for item in res_json["data"]]
                    embeddings.extend(chunk_embeddings)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise RuntimeError(f"OpenAI Embedding API failed: {e}")
                    time.sleep(2 ** attempt)
                    
        return embeddings


class LocalHashEmbedder(BaseEmbedder):
    """
    A lightweight, deterministic feature hashing (Signed Hash Vectorization) embedder.
    Provides fixed-size 768-dimensional dense vectors representing word occurrences.
    Useful for local offline testing and quick evaluations.
    """
    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        return self._hash_vectorize(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_vectorize(t) for t in texts]

    def _hash_vectorize(self, text: str) -> List[float]:
        vector = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vector.tolist()
            
        for word in words:
            # Hash to find index
            h_str = hashlib.md5(word.encode('utf-8')).hexdigest()
            h = int(h_str, 16)
            index = h % self.dimension
            # Signed hashing to reduce collision effects
            sign = 1 if ((h // self.dimension) % 2 == 0) else -1
            vector[index] += sign
            
        # L2 normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()


def get_embedder(provider: str = None, api_key: str = None) -> BaseEmbedder:
    """
    Factory function to get an embedder based on provider and keys.
    """
    if not provider:
        provider = config.DEFAULT_EMBEDDING_PROVIDER
        
    provider = provider.lower()
    
    if provider == "gemini":
        key = api_key or config.GEMINI_API_KEY
        if key:
            return GeminiEmbedder(key)
    elif provider == "openai":
        key = api_key or config.OPENAI_API_KEY
        if key:
            return OpenAIEmbedder(key)
            
    # Fallback to local
    return LocalHashEmbedder()
