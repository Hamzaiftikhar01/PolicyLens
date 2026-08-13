import re
from typing import List, Dict, Any, Set
import numpy as np
from app.core.embeddings import get_embedder

def clean_tokens(text: str) -> Set[str]:
    """Tokenizes text and removes small/common words to compare content."""
    stopwords = {"the", "a", "an", "and", "or", "but", "if", "then", "of", "at", "by", "for", "with", "about", "to", "in", "on", "is", "are", "was", "were", "be", "been", "being", "that", "this", "these", "those"}
    words = re.findall(r'\b\w{3,20}\b', text.lower())
    return set(w for w in words if w not in stopwords)

def calculate_retrieval_metrics(
    retrieved_chunks: List[Dict[str, Any]], 
    expected_docs: List[str], 
    expected_sections: List[str]
) -> Dict[str, float]:
    """
    Calculates retrieval metrics: Hit@5, Recall@5, and Precision@5.
    If expected_sections is empty (unanswerable question), the ideal retrieval is empty.
    """
    if not expected_docs and not expected_sections:
        # For unanswerable questions, if no chunks are retrieved (or scores are weak), it is a perfect hit
        is_empty_retrieval = len(retrieved_chunks) == 0
        return {
            "hit_at_k": 1.0 if is_empty_retrieval else 0.0,
            "recall_at_k": 1.0 if is_empty_retrieval else 0.0,
            "precision_at_k": 1.0 if is_empty_retrieval else 0.0
        }
        
    retrieved_docs = set(c["document_id"] for c in retrieved_chunks)
    
    # Extract clean section names from retrieved chunks (e.g. "Article 25" or "Section 379")
    retrieved_sections = set()
    for c in retrieved_chunks:
        sec = c.get("section", "")
        if sec:
            retrieved_sections.add(sec.strip())
            
    # Calculate Hit@K: at least one expected section is retrieved (or expected doc if sections not specified)
    hit = 0.0
    if expected_sections:
        matches = [s for s in expected_sections if s in retrieved_sections]
        if matches:
            hit = 1.0
    else:
        matches = [d for d in expected_docs if d in retrieved_docs]
        if matches:
            hit = 1.0
            
    # Calculate Recall@K: proportion of expected sections retrieved
    recall = 0.0
    if expected_sections:
        matched_sections = [s for s in expected_sections if s in retrieved_sections]
        recall = len(matched_sections) / len(expected_sections)
    else:
        matched_docs = [d for d in expected_docs if d in retrieved_docs]
        recall = len(matched_docs) / len(expected_docs) if expected_docs else 1.0
        
    # Calculate Precision@K: proportion of retrieved chunks that are relevant
    precision = 0.0
    if retrieved_chunks:
        relevant_count = 0
        for c in retrieved_chunks:
            doc_match = c["document_id"] in expected_docs
            sec_match = c.get("section") in expected_sections if expected_sections else True
            if doc_match and sec_match:
                relevant_count += 1
        precision = relevant_count / len(retrieved_chunks)
        
    return {
        "hit_at_k": hit,
        "recall_at_k": recall,
        "precision_at_k": precision
    }

def calculate_groundedness(
    answer: str, 
    citations: List[Dict[str, Any]], 
    evidence_status: str,
    api_key: str = None,
    provider: str = None
) -> float:
    """
    Measures groundedness: is the generated answer fully supported by the cited sources?
    Returns a score between 0.0 and 1.0.
    """
    if evidence_status == "insufficient":
        # If the pipeline correctly identifies insufficient evidence and answers fallback, it's 100% grounded
        if "insufficient" in answer.lower() or "couldn't find" in answer.lower():
            return 1.0
            
    if not citations:
        # An answer without citations is ungrounded (unless it was a correct fallback)
        if "insufficient" in answer.lower() or "couldn't find" in answer.lower():
            return 1.0
        return 0.0
        
    # Concatenate all cited source text
    source_corpus = " ".join(c["text"] for c in citations)
    
    # Calculate word overlap ratio (offline check)
    answer_tokens = clean_tokens(answer)
    source_tokens = clean_tokens(source_corpus)
    
    if not answer_tokens:
        return 1.0
        
    # Check how many answer words are present in source text
    overlap_count = sum(1 for t in answer_tokens if t in source_tokens)
    overlap_ratio = overlap_count / len(answer_tokens)
    
    # Boost factor: if we have strong overlap, score is high
    # Clean text overlap is a good indicator of lexical grounding
    return min(1.0, overlap_ratio * 1.2)


def calculate_answer_relevance(
    answer: str, 
    expected_answer: str,
    api_key: str = None,
    provider: str = None
) -> float:
    """
    Measures answer relevance compared to the ground truth answer.
    Uses cosine similarity of local hash embeddings for an offline, deterministic metric.
    """
    embedder = get_embedder(provider=provider, api_key=api_key)
    
    try:
        vec_ans = embedder.embed_query(answer)
        vec_exp = embedder.embed_query(expected_answer)
        
        # Calculate cosine similarity
        v1 = np.array(vec_ans)
        v2 = np.array(vec_exp)
        
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 > 0 and norm2 > 0:
            sim = dot / (norm1 * norm2)
            # Clip between 0 and 1
            return float(max(0.0, min(1.0, sim)))
        return 0.0
    except Exception:
        # Simple fallback token overlap
        t1 = clean_tokens(answer)
        t2 = clean_tokens(expected_answer)
        if not t1 or not t2:
            return 0.0
        intersection = t1.intersection(t2)
        return len(intersection) / max(len(t1), len(t2))


def calculate_citation_accuracy(
    citations: List[Dict[str, Any]], 
    expected_sections: List[str]
) -> float:
    """
    Measures citation accuracy: are the cited articles/sections the expected ones?
    """
    if not expected_sections:
        # Unanswerable question
        return 1.0 if not citations else 0.0
        
    if not citations:
        return 0.0
        
    cited_sections = set(c["section"] for c in citations)
    
    correct_citations = sum(1 for s in cited_sections if s in expected_sections)
    
    # Citation accuracy is ratio of correct citations to total cited sections
    return correct_citations / len(cited_sections)
