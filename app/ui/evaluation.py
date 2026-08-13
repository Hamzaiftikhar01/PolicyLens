from fastapi import APIRouter, BackgroundTasks, HTTPException
from pathlib import Path
import csv
import sys
import subprocess
import config

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])

# Simple in-memory tracker for running evaluation
_eval_status = {
    "is_running": False,
    "last_run_time": None,
    "error": None
}

def run_eval_subprocess():
    """Background task to run the evaluate.py script."""
    global _eval_status
    _eval_status["is_running"] = True
    _eval_status["error"] = None
    
    script_path = config.BASE_DIR / "evaluation" / "evaluate.py"
    
    try:
        # Run subprocess with current Python executable
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[EVAL SUBPROCESS SUCCESS]\n{result.stdout[-1000:]}")
    except subprocess.CalledProcessError as e:
        _eval_status["error"] = f"Evaluation script exited with code {e.returncode}. Error: {e.stderr[-1000:]}"
        print(f"[EVAL SUBPROCESS ERROR] {e.stderr}")
    except Exception as e:
        _eval_status["error"] = f"Unexpected error: {str(e)}"
        print(f"[EVAL SUBPROCESS EXCEPTION] {e}")
    finally:
        _eval_status["is_running"] = False

@router.post("/run")
def start_evaluation(background_tasks: BackgroundTasks):
    """Triggers the evaluation script asynchronously in the background."""
    global _eval_status
    if _eval_status["is_running"]:
        return {"status": "running", "message": "Evaluation is already in progress."}
        
    background_tasks.add_task(run_eval_subprocess)
    return {"status": "started", "message": "Evaluation run has been started in the background."}

@router.get("/status")
def get_evaluation_status():
    """Returns the current background status of the evaluation run."""
    return _eval_status

@router.get("/results")
def get_evaluation_results():
    """Reads and returns the parsed CSV results and markdown reports from disk."""
    eval_dir = config.BASE_DIR / "evaluation"
    csv_path = eval_dir / "results.csv"
    report_path = eval_dir / "report.md"
    failure_path = eval_dir / "failure_analysis.md"
    
    if not csv_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Evaluation has not been run yet or results are missing."
        )
        
    results_list = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results_list.append({
                    "id": int(row["id"]),
                    "question": row["question"],
                    "type": row["type"],
                    "difficulty": row["difficulty"],
                    "latency": float(row["latency"]),
                    "cost": float(row["cost"]),
                    "hit_at_5": float(row["hit_at_5"]),
                    "recall_at_5": float(row["recall_at_5"]),
                    "groundedness": float(row["groundedness"]),
                    "relevance": float(row["relevance"]),
                    "citation_accuracy": float(row["citation_accuracy"]),
                    "evidence_status": row["evidence_status"]
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read evaluation results CSV: {str(e)}")
        
    report_md = ""
    if report_path.exists():
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_md = f.read()
        except Exception:
            pass
            
    failure_md = ""
    if failure_path.exists():
        try:
            with open(failure_path, "r", encoding="utf-8") as f:
                failure_md = f.read()
        except Exception:
            pass
            
    return {
        "results": results_list,
        "report_md": report_md,
        "failure_md": failure_md
    }
