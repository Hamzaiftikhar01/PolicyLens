import os
import json
import time
import csv
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from app.core.pdf import extract_pdf_chunks
from app.core.embeddings import get_embedder
from app.core.vector_store import get_vector_store
from app.core.rag import run_rag_pipeline
from evaluation.metrics import (
    calculate_retrieval_metrics, 
    calculate_groundedness, 
    calculate_answer_relevance, 
    calculate_citation_accuracy
)

def build_benchmark_index():
    """
    Builds the FAISS vector index for the frozen benchmark corpus.
    Loads PDFs, chunks them structurally, embeds them, and saves the vector store.
    """
    print("[*] Checking benchmark vector index...")
    vector_store = get_vector_store("benchmark")
    
    if not vector_store.is_empty:
        print("[OK] Benchmark index already exists. Skipping ingestion.")
        return
        
    print("[*] Index not found or empty. Beginning ingestion process...")
    metadata_path = config.BENCHMARK_DIR / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"[ERROR] Metadata file {metadata_path} is missing. Cannot ingest.")
        
    with open(metadata_path, "r") as f:
        documents = json.load(f)
        
    # Check if any PDFs exist
    missing_pdfs = []
    for doc in documents:
        pdf_path = config.BENCHMARK_DIR / doc["filename"]
        if not pdf_path.exists():
            missing_pdfs.append(doc["filename"])
            
    if missing_pdfs:
        print(f"[!] Warning: The following required PDFs are missing from {config.BENCHMARK_DIR}:")
        for p in missing_pdfs:
            print(f"  - {p}")
        print("\n[*] Attempting to run download utility script...")
        
        # Import and run download script programmatically
        try:
            import scripts.download_benchmark as downloader
            downloader.main()
        except Exception as e:
            print(f"[ERROR] Could not run downloader script automatically: {e}")
            
        # Re-check missing PDFs
        still_missing = [p for p in missing_pdfs if not (config.BENCHMARK_DIR / p).exists()]
        if still_missing:
            print("\n[WARNING] Some official PDFs are missing and could not be fetched.")
            print("PolicyLens will proceed to index only the available documents.")
            print("To evaluate all cases, please place the missing PDFs manually in 'data/benchmark'.")
            
    print("\n==================================================")
    print(" Ingesting Legal Documents & Building Index")
    print("==================================================")
    
    all_chunks = []
    embedder = get_embedder()
    
    for doc in documents:
        pdf_path = config.BENCHMARK_DIR / doc["filename"]
        if not pdf_path.exists():
            print(f"[-] Skipping missing document: {doc['title']}")
            continue
            
        print(f"[*] Extracting structural chunks from: {doc['title']}...")
        
        # Capture metadata
        doc_metadata = {
            "source": doc["source"],
            "source_url": doc["source_url"],
            "category": doc["category"],
            "date": doc["date"],
            "version": doc["version"]
        }
        
        # Extract structural legal chunks
        chunks = extract_pdf_chunks(
            pdf_path=pdf_path,
            document_id=doc["document_id"],
            document_title=doc["title"],
            doc_metadata=doc_metadata,
            chunk_size=config.DEFAULT_CHUNK_SIZE,
            overlap=config.DEFAULT_CHUNK_OVERLAP
        )
        
        print(f"  Generated {len(chunks)} chunks.")
        all_chunks.extend(chunks)
        
    if not all_chunks:
        print("[ERROR] No chunks extracted because all benchmark PDFs are missing.")
        return
        
    print(f"\n[*] Generating embeddings for {len(all_chunks)} chunks...")
    texts = [c["text"] for c in all_chunks]
    
    t0 = time.time()
    embeddings = embedder.embed_documents(texts)
    t_emb = time.time() - t0
    print(f"  Embeddings generated in {t_emb:.2f} seconds.")
    
    print("[*] Writing chunks to FAISS vector store...")
    vector_store.add_documents(all_chunks, embeddings)
    print("[OK] Benchmark corpus ingestion complete.")
    print("==================================================\n")

def run_evaluation():
    """Runs the RAG pipeline over the evaluation dataset and writes reports."""
    build_benchmark_index()
    
    questions_path = Path(__file__).resolve().parent / "questions.json"
    if not questions_path.exists():
        raise FileNotFoundError(f"[ERROR] Evaluation questions file not found at {questions_path}")
        
    with open(questions_path, "r") as f:
        cases = json.load(f)
        
    print("==================================================")
    print(f" Running PolicyLens RAG Evaluation: {len(cases)} Cases")
    print("==================================================")
    
    results = []
    latencies = []
    
    # Store parameters
    provider = config.DEFAULT_LLM_PROVIDER
    model = config.LLM_MODELS[provider]
    embed_model = config.EMBEDDING_MODELS[config.DEFAULT_EMBEDDING_PROVIDER]
    
    results_dir = Path(__file__).resolve().parent
    csv_file = results_dir / "results.csv"
    report_file = results_dir / "report.md"
    failure_file = results_dir / "failure_analysis.md"
    
    # Run evaluation
    for case in cases:
        q_id = case["id"]
        q_text = case["question"]
        expected_docs = case["expected_documents"]
        expected_sections = case["expected_sections"]
        q_type = case["question_type"]
        
        print(f"\n[*] [{q_id}/{len(cases)}] Type: {q_type} | Q: {q_text[:60]}...")
        
        # Execute actual RAG pipeline
        rag_res = run_rag_pipeline(
            question=q_text,
            namespace="benchmark",
            top_k=config.DEFAULT_TOP_K
        )
        
        # Extract results
        answer = rag_res["answer"]
        citations = rag_res["citations"]
        evidence_status = rag_res["evidence_status"]
        latency = rag_res["latency"]
        cost = rag_res["cost"]
        
        latencies.append(latency)
        
        # Calculate scores
        # We need the vector store to fetch retrieved chunks for retrieval metric calculation
        vector_store = get_vector_store("benchmark")
        embedder = get_embedder()
        query_vector = embedder.embed_query(q_text)
        retrieved_results = vector_store.search(query_vector, top_k=config.DEFAULT_TOP_K)
        retrieved_chunks = [r[0] for r in retrieved_results]
        
        ret_metrics = calculate_retrieval_metrics(retrieved_chunks, expected_docs, expected_sections)
        hit_score = ret_metrics["hit_at_k"]
        recall_score = ret_metrics["recall_at_k"]
        
        groundedness = calculate_groundedness(answer, citations, evidence_status)
        relevance = calculate_answer_relevance(answer, case["expected_answer"])
        citation_acc = calculate_citation_accuracy(citations, expected_sections)
        
        results.append({
            "id": q_id,
            "question": q_text,
            "type": q_type,
            "difficulty": case["difficulty"],
            "latency": latency,
            "cost": cost,
            "hit_at_5": hit_score,
            "recall_at_5": recall_score,
            "groundedness": groundedness,
            "relevance": relevance,
            "citation_accuracy": citation_acc,
            "answer": answer,
            "expected_answer": case["expected_answer"],
            "citations_count": len(citations),
            "evidence_status": evidence_status
        })
        
        print(f"  Results - Hit@5: {hit_score:.1f} | Groundedness: {groundedness:.2f} | Citation Acc: {citation_acc:.2f} | Latency: {latency:.2f}s")

    # Aggregate metrics
    total_cases = len(results)
    avg_hit = np.mean([r["hit_at_5"] for r in results])
    avg_recall = np.mean([r["recall_at_5"] for r in results])
    avg_groundedness = np.mean([r["groundedness"] for r in results])
    avg_relevance = np.mean([r["relevance"] for r in results])
    avg_citation_acc = np.mean([r["citation_accuracy"] for r in results])
    
    avg_latency = np.mean(latencies)
    median_latency = np.median(latencies)
    total_cost = sum(r["cost"] for r in results)
    avg_cost = total_cost / total_cases if total_cases > 0 else 0.0
    
    # Save CSV
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\n[OK] Results logged to: {csv_file}")
    
    # Generate report.md
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"""# PolicyLens Evaluation Report

This report presents the system evaluation metrics for PolicyLens generated by running the automated harness against the **Pakistan Legal & Policy Corpus** (Benchmark Mode).

## System Configuration
* **LLM Provider**: `{provider.upper()}` ({model})
* **Embedding Provider**: `{config.DEFAULT_EMBEDDING_PROVIDER.upper()}` ({embed_model})
* **Vector Index**: FAISS (`IndexFlatIP`, Cosine Similarity)
* **Default Chunk Size**: `{config.DEFAULT_CHUNK_SIZE}` characters
* **Default Chunk Overlap**: `{config.DEFAULT_CHUNK_OVERLAP}` characters
* **Top-K Chunks**: `{config.DEFAULT_TOP_K}`
* **Date Evaluated**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Performance Summary

| Metric | Score / Value | Description |
|:---|:---|:---|
| **Total Test Questions** | {total_cases} | Evaluation test coverage size |
| **Retrieval Hit@5** | {avg_hit * 100:.1f}% | Percentage of queries where expected source was retrieved |
| **Retrieval Recall@5** | {avg_recall * 100:.1f}% | Ratio of expected sections retrieved to total expected |
| **Groundedness** | {avg_groundedness * 100:.1f}% | Answer contains only statements supported by cited sources |
| **Answer Relevance** | {avg_relevance * 100:.1f}% | Semantic similarity to golden reference answers |
| **Citation Accuracy** | {avg_citation_acc * 100:.1f}% | Percentage of cited sections that match gold labels |
| **Average Latency** | {avg_latency:.2f} sec | Mean query response time |
| **Median Latency** | {median_latency:.2f} sec | 50th percentile query response time |
| **Average Cost / Request** | ${avg_cost:.6f} | Average API consumption cost |
| **Total Run Cost** | ${total_cost:.4f} | Sum of API costs for this evaluation run |

## Performance by Question Type

| Question Type | Count | Hit@5 | Groundedness | Citation Acc | Relevance |
|:---|:---:|:---:|:---:|:---:|:---:|
""")
        
        # Group metrics by type
        types = set(r["type"] for r in results)
        for t in sorted(types):
            type_res = [r for r in results if r["type"] == t]
            t_count = len(type_res)
            t_hit = np.mean([r["hit_at_5"] for r in type_res])
            t_ground = np.mean([r["groundedness"] for r in type_res])
            t_cit = np.mean([r["citation_accuracy"] for r in type_res])
            t_rel = np.mean([r["relevance"] for r in type_res])
            f.write(f"| {t} | {t_count} | {t_hit*100:.1f}% | {t_ground*100:.1f}% | {t_cit*100:.1f}% | {t_rel*100:.1f}% |\n")
            
        f.write("\n## Detailed Case Metrics\n\n")
        f.write("| ID | Question | Difficulty | Hit@5 | Groundedness | Citation Acc | Latency | Status |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in results:
            indicator = "✓" if r["hit_at_5"] > 0.9 and r["groundedness"] > 0.9 else "⚠"
            if r["evidence_status"] == "insufficient" and r["groundedness"] > 0.9:
                indicator = "✓ (Fallback)"
            f.write(f"| {r['id']} | {r['question'][:50]}... | {r['difficulty']} | {r['hit_at_5']*100:.0f}% | {r['groundedness']*100:.0f}% | {r['citation_accuracy']*100:.0f}% | {r['latency']:.2f}s | {indicator} |\n")
            
    print(f"[OK] Evaluation report created: {report_file}")
    
    # Generate failure_analysis.md
    # Identify cases where groundedness < 0.85, or citation accuracy < 0.85, or hit_at_5 == 0.0
    failures = [r for r in results if r["hit_at_5"] < 0.9 or r["groundedness"] < 0.85 or r["citation_accuracy"] < 0.85]
    
    with open(failure_file, "w", encoding="utf-8") as f:
        f.write("# PolicyLens Failure & Weakness Analysis\n\n")
        f.write("This document summarizes the analyzed failure cases and pipeline weaknesses observed during the evaluation run.\n\n")
        
        if not failures:
            f.write("## No Critical Failures Observed\n\n")
            f.write("The system performed exceptionally well. All questions met the groundedness and citation accuracy thresholds. ")
            f.write("However, we document two potential architectural failure scenarios for legal RAG pipelines below as representative references:\n\n")
            
            # Write two representative potential failure analyses
            f.write("""### REFERENCE CASE 1: Semantic Defamation Terminology Mismatch (CPC vs PECA)
* **Question**: Compare the jurisdiction and procedure for defamation between the Pakistan Penal Code (PPC) and PECA.
* **Failure Type**: Semantic Terminology Mismatch.
* **Root Cause**: Defamation in the Penal Code (Section 500) and defaming an individual online under PECA (Section 20) are stored in different legal chapters. A basic retriever may miss the comparative alignment and prioritize general civil defamation cases due to dense embedding alignment prioritizing the term "defamation lawsuit" instead of criminal cybercrime courts.
* **Proposed Improvement**: Implement query expansion to automatically inject keywords like "online defamation", "cyber libel", and "Section 20 PECA" into the query, or use a reciprocal rank fusion (RRF) retriever combining dense semantic search with sparse BM25 search.

### REFERENCE CASE 2: Insufficient Citation Mapping (Multi-Section / Complex)
* **Question**: What are the fundamental rights regarding security of person and fair trial under the Constitution?
* **Failure Type**: Insufficient Citation Mapping.
* **Root Cause**: The answer spans two separate constitutional Articles (Article 9 and Article 10A). In some chunk sizes, these provisions fall into separate vector spaces. If chunk size is too small or top-K is set too low (e.g. K=3), the retriever fails to load both provisions concurrently, leading to an incomplete answer that only cites one Article.
* **Proposed Improvement**: Adjust top-K to 5 or implement parent-child retrieval where small retrieved child chunks automatically pull their surrounding parent document sections to supply the LLM with complete contextual coverage.
""")
        else:
            f.write(f"## Observed Failures / Weaknesses ({len(failures)} cases)\n\n")
            for idx, fail in enumerate(failures[:3]):
                f.write(f"### CASE {idx + 1}: Question {fail['id']} - {fail['type']}\n")
                f.write(f"* **Question**: \"{fail['question']}\"\n")
                f.write(f"* **Expected Sections**: `{fail['expected_answer'][:150]}...`\n")
                f.write(f"* **Observed Answer**: \"{fail['answer'][:200]}...\"\n")
                
                # Deduce failure type
                if fail["hit_at_5"] == 0.0:
                    fail_type = "Retrieval Failure (0% Hit Rate)"
                    cause = "The embedding vector for the question did not align close enough with the target document chunks in the vector space, resulting in relevant paragraphs falling outside the Top-K retrieved items."
                    improvement = "Increase chunk overlap and tune dense embedding thresholds, or supplement search with keyword-based retrieval (hybrid BM25)."
                elif fail["groundedness"] < 0.85:
                    fail_type = "Hallucination / Weak Grounding"
                    cause = "The LLM introduced background information or legal assumptions not explicitly present in the retrieved passages. This occurs when instructions regarding strict grounding are overridden by the model's pre-trained knowledge."
                    improvement = "Increase the system prompt constraint weights or use a more rigorous model like Gemini 1.5 Pro to enforce strict citation bounds."
                else:
                    fail_type = "Citation Mismatch / Incorrect Reference"
                    cause = "The LLM successfully generated facts from the context but associated them with the wrong Source labels, or hallucinated Source references that did not exist in the retrieved context list."
                    improvement = "Implement post-generation regex filters to inspect citations and map them strictly against source list bounds."
                    
                f.write(f"* **Failure Type**: {fail_type}\n")
                f.write(f"* **Root Cause**: {cause}\n")
                f.write(f"* **Proposed Improvement**: {improvement}\n\n")
                
    print(f"[OK] Failure analysis report created: {failure_file}")
    print("==================================================")

if __name__ == "__main__":
    run_evaluation()
