import time
import re
from typing import Dict, Any, List, Tuple
import config
from app.core.embeddings import get_embedder
from app.core.vector_store import get_vector_store
from app.core.llm import get_llm

def clean_citations_in_text(text: str) -> str:
    """Normalizes citations in LLM text (e.g. [Source1] -> [Source 1], [1] -> [Source 1])."""
    # [Source1] or [Source 1] -> [Source 1]
    text = re.sub(r'\[Source\s*(\d+)\]', r'[Source \1]', text)
    # [1] -> [Source 1] (only if it's likely a citation, i.e., preceded by sentence content)
    # text = re.sub(r'(?<=\w)\s*\[(\d+)\]', r' [Source \1]', text)
    return text

def parse_citations(text: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts citations from generated text, mapping '[Source X]' references
    to actual metadata. Clears out hallucinated citations that don't match retrieved chunks.
    """
    text = clean_citations_in_text(text)
    
    # Find all pattern occurrences [Source X]
    citation_matches = re.findall(r'\[Source\s*(\d+)\]', text)
    unique_ids = sorted(list(set(int(m) for m in citation_matches)))
    
    citations = []
    valid_ids = {}
    
    for c_id in unique_ids:
        idx = c_id - 1
        if 0 <= idx < len(retrieved_chunks):
            chunk = retrieved_chunks[idx]
            citations.append({
                "id": c_id,
                "source_label": f"[Source {c_id}]",
                "document_id": chunk["document_id"],
                "document_title": chunk["document_title"],
                "section": chunk["section"],
                "page": chunk["page"],
                "text": chunk["text"],
                "metadata": chunk.get("metadata", {})
            })
            valid_ids[c_id] = len(citations)  # map old ID to new sequential ID
            
    # Re-map citations in the text to match the final sequential citations list
    def replace_citation(match):
        old_id = int(match.group(1))
        if old_id in valid_ids:
            new_idx = list(valid_ids.keys()).index(old_id) + 1
            return f"[{new_idx}]"
        return ""  # Remove invalid / hallucinated citations
        
    text_processed = re.sub(r'\[Source\s*(\d+)\]', replace_citation, text)
    
    # Also adjust the citation objects IDs to be clean sequential [1], [2], ...
    for i, c in enumerate(citations):
        c["id"] = i + 1
        c["source_label"] = f"[{i + 1}]"
        
    return text_processed, citations

def run_rag_pipeline(
    question: str,
    namespace: str,
    top_k: int = None,
    api_key_override: str = None,
    provider_override: str = None
) -> Dict[str, Any]:
    """
    Executes the complete citation-grounded RAG pipeline.
    """
    t_start = time.time()
    
    if top_k is None:
        top_k = config.DEFAULT_TOP_K
        
    pipeline_steps = {}
    
    # 1. Initialize Clients
    t_init_start = time.time()
    embedder = get_embedder(provider=provider_override, api_key=api_key_override)
    llm = get_llm(provider=provider_override, api_key=api_key_override)
    vector_store = get_vector_store(namespace)
    pipeline_steps["initialize"] = time.time() - t_init_start
    
    # Case 1: Empty Database
    if vector_store.is_empty:
        total_time = time.time() - t_start
        return {
            "question": question,
            "answer": "I couldn't find sufficient evidence in the available documents to answer this question. The document index is currently empty.",
            "evidence_status": "insufficient",
            "citations": [],
            "conflict_detected": False,
            "latency": total_time,
            "cost": 0.0,
            "pipeline_steps": {**pipeline_steps, "search": 0, "generate": 0}
        }
        
    # 2. Embed Query & Retrieve
    t_embed_start = time.time()
    try:
        query_vector = embedder.embed_query(question)
        pipeline_steps["embedding"] = time.time() - t_embed_start
        
        # 3. Retrieve
        t_ret_start = time.time()
        retrieved_results = vector_store.search(query_vector, top_k=top_k)
        pipeline_steps["retrieval"] = time.time() - t_ret_start
        
        chunks = [r[0] for r in retrieved_results]
        scores = [r[1] for r in retrieved_results]
    except Exception as e:
        print(f"[WARNING] Dense query embedding/retrieval failed ({e}). Falling back to local offline keyword search.")
        pipeline_steps["embedding"] = time.time() - t_embed_start
        
        t_ret_start = time.time()
        # Perform fallback keyword search over metadata chunks
        words = [w.lower() for w in re.findall(r'\w+', question) if len(w) > 2]
        if not words:
            words = [w.lower() for w in re.findall(r'\w+', question)]
            
        scored_chunks = []
        for chunk in vector_store.chunks:
            text = chunk["text"].lower()
            score = 0.0
            for word in words:
                count = text.count(word)
                if count > 0:
                    score += count * 1.5
            scored_chunks.append((chunk, score))
            
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        retrieved_results = scored_chunks[:top_k]
        
        pipeline_steps["retrieval"] = time.time() - t_ret_start
        
        chunks = [r[0] for r in retrieved_results if r[1] > 0]
        scores = [0.70 for r in retrieved_results if r[1] > 0]
        
        # Override LLM client to also use local fallback
        llm = get_llm("local")
    
    # Determine thresholds based on whether the embedder is local (sparse hashing) or dense
    is_local = embedder.__class__.__name__ == "LocalHashEmbedder"
    weak_threshold = 0.015 if is_local else config.THRESHOLD_WEAK
    strong_threshold = 0.060 if is_local else config.THRESHOLD_STRONG
    
    # Case 2: Empty Retrieval / Scores below weak threshold
    max_score = scores[0] if scores else 0.0
    
    if not chunks or max_score < weak_threshold:
        total_time = time.time() - t_start
        return {
            "question": question,
            "answer": "The available documents do not contain sufficiently relevant evidence to answer this question reliably.",
            "evidence_status": "insufficient",
            "citations": [],
            "conflict_detected": False,
            "latency": total_time,
            "cost": 0.0,
            "pipeline_steps": {**pipeline_steps, "generate": 0}
        }
        
    # Determine evidence strength
    if max_score >= strong_threshold:
        evidence_status = "strong"
    else:
        evidence_status = "limited"
        
    # 4. Construct Context
    context_lines = []
    for i, chunk in enumerate(chunks):
        context_lines.append(
            f"[Source {i+1}]\n"
            f"Document: {chunk['document_title']}\n"
            f"Section: {chunk['section']}\n"
            f"Page: {chunk['page']}\n"
            f"Content: {chunk['text']}\n"
        )
    context_str = "\n".join(context_lines)
    
    # 5. Generate Grounded Answer
    t_gen_start = time.time()
    try:
        llm_res = llm.generate(question, context_str)
    except Exception as e:
        print(f"[WARNING] Live LLM generation failed ({e}). Falling back to local offline generation.")
        from app.core.llm import LocalFallbackLLM
        fallback_llm = LocalFallbackLLM()
        llm_res = fallback_llm.generate(question, context_str)
    pipeline_steps["generation"] = time.time() - t_gen_start
    
    raw_answer = llm_res["text"]
    
    # 6. Parse and Map Citations
    processed_answer, citations = parse_citations(raw_answer, chunks)
    
    # 7. Conflict Detection
    # If LLM indicates a conflict, or if retrieved documents show contrasting statements
    conflict_terms = ["conflict", "contradict", "differing view", "differing penalties", "however, another section", "contrary to"]
    conflict_detected = any(term in processed_answer.lower() for term in conflict_terms)
    
    # Calculate costs
    cost = llm_res.get("cost", 0.0)
    
    total_time = time.time() - t_start
    
    return {
        "question": question,
        "answer": processed_answer,
        "evidence_status": evidence_status,
        "citations": citations,
        "conflict_detected": conflict_detected,
        "latency": total_time,
        "cost": cost,
        "pipeline_steps": pipeline_steps
    }
