import uvicorn
from pathlib import Path
import sys

# Ensure path resolution
sys.path.append(str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import os
    # Enable reload only for local development (default to False in cloud containers)
    is_dev = os.getenv("EMBEDDING_PROVIDER", "").lower() == "local" or os.getenv("ENV", "").lower() == "development"
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=is_dev)
