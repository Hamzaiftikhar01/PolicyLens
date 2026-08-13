import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from app.core.embeddings import get_embedder, LocalHashEmbedder
from app.core.vector_store import VectorStore
from app.core.pdf import clean_text, split_text_sliding_window
from app.core.rag import parse_citations

def test_local_embedder():
    """Verifies that the LocalHashEmbedder produces valid vectors of the correct dimension."""
    embedder = get_embedder("local")
    assert isinstance(embedder, LocalHashEmbedder)
    
    vec = embedder.embed_query("test query text")
    assert len(vec) == 768
    assert isinstance(vec, list)
    assert isinstance(vec[0], float)
    
    # Test normalization
    v_arr = np.array(vec)
    norm = np.linalg.norm(v_arr)
    # Norm should be close to 1
    assert abs(norm - 1.0) < 1e-5

def test_text_cleanup():
    """Verifies text cleansing and sliding window splitting functions."""
    raw = "  This is a   sentence. \n New line here.  "
    clean = clean_text(raw)
    assert clean == "This is a sentence. New line here."
    
    # Sliding window test
    chunks = split_text_sliding_window(clean, chunk_size=10, overlap=2)
    assert len(chunks) > 0
    assert chunks[0] == "This is a "

def test_vector_store(tmp_path):
    """Verifies VectorStore initialization, adding documents, saving, loading, and searching."""
    vs = VectorStore(index_dir=tmp_path, dimension=128)
    assert vs.is_empty
    
    # Add dummy chunks
    chunks = [
        {"chunk_id": "ch_01", "document_id": "doc_1", "document_title": "Doc 1", "text": "This is sample article 1", "page": 1, "section": "Article 1"},
        {"chunk_id": "ch_02", "document_id": "doc_1", "document_title": "Doc 1", "text": "This is sample article 2", "page": 2, "section": "Article 2"}
    ]
    # Generate dummy normalized embeddings
    emb = [
        np.random.normal(size=128).tolist(),
        np.random.normal(size=128).tolist()
    ]
    # Normalize
    emb = [(e / np.linalg.norm(e)).tolist() for e in emb]
    
    vs.add_documents(chunks, emb)
    assert not vs.is_empty
    assert len(vs.chunks) == 2
    
    # Search
    search_q = emb[0]
    res = vs.search(search_q, top_k=2)
    assert len(res) == 2
    # First match should be chunk 1 since we queried with its embedding
    assert res[0][0]["chunk_id"] == "ch_01"
    assert res[0][1] > 0.9  # High similarity score

def test_citation_parsing():
    """Verifies that the citation parser correctly links LLM source tags to chunk metadata."""
    retrieved_chunks = [
        {"document_id": "doc_1", "document_title": "Title 1", "section": "Article 12", "page": 4, "text": "Passage 1 text"},
        {"document_id": "doc_2", "document_title": "Title 2", "section": "Section 99", "page": 15, "text": "Passage 2 text"}
    ]
    
    raw_answer = "This statement is supported by [Source 1]. Another statement is supported by [Source 2]. An invalid citation is [Source 3]."
    
    answer, citations = parse_citations(raw_answer, retrieved_chunks)
    
    # [Source 1] -> [1], [Source 2] -> [2], [Source 3] should be removed as it's invalid
    assert "[1]" in answer
    assert "[2]" in answer
    assert "[3]" not in answer
    
    assert len(citations) == 2
    assert citations[0]["id"] == 1
    assert citations[0]["document_title"] == "Title 1"
    assert citations[0]["section"] == "Article 12"
    assert citations[0]["page"] == 4
    
    assert citations[1]["id"] == 2
    assert citations[1]["document_title"] == "Title 2"
    assert citations[1]["section"] == "Section 99"
    assert citations[1]["page"] == 15
