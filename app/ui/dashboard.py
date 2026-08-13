from fastapi import APIRouter
from pathlib import Path
import json
import csv
import sys
import config
from app.core.vector_store import get_vector_store

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_stats():
    """Returns database and evaluation statistics for the dashboard."""
    # 1. Check Benchmark Index Status
    benchmark_vs = get_vector_store("benchmark")
    is_indexed = not benchmark_vs.is_empty
    total_chunks = len(benchmark_vs.chunks) if is_indexed else 0
    
    # 2. Get Benchmark Document Count from Metadata
    meta_path = config.BENCHMARK_DIR / "metadata.json"
    doc_count = 0
    if meta_path.exists():
        try:
            with open(meta_path, "r") as f:
                docs = json.load(f)
                doc_count = len(docs)
        except Exception:
            pass
            
    # 3. Read Evaluation Results if available
    eval_dir = config.BASE_DIR / "evaluation"
    csv_path = eval_dir / "results.csv"
    
    eval_stats = None
    if csv_path.exists():
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    avg_hit = sum(float(r["hit_at_5"]) for r in rows) / len(rows)
                    avg_ground = sum(float(r["groundedness"]) for r in rows) / len(rows)
                    avg_rel = sum(float(r["relevance"]) for r in rows) / len(rows)
                    avg_cit = sum(float(r["citation_accuracy"]) for r in rows) / len(rows)
                    avg_latency = sum(float(r["latency"]) for r in rows) / len(rows)
                    
                    eval_stats = {
                        "total_questions": len(rows),
                        "hit_at_5": f"{avg_hit * 100:.1f}%",
                        "groundedness": f"{avg_ground * 100:.1f}%",
                        "citation_accuracy": f"{avg_cit * 100:.1f}%",
                        "relevance": f"{avg_rel * 100:.1f}%",
                        "avg_latency": f"{avg_latency:.2f}s"
                    }
        except Exception:
            pass
            
    return {
        "status": "Indexed" if is_indexed else "Not Indexed",
        "benchmark_documents": doc_count,
        "benchmark_chunks": total_chunks,
        "benchmark_questions": 20,
        "evaluation_metrics": eval_stats
    }
