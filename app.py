import uvicorn
from pathlib import Path
import sys

# Ensure path resolution
sys.path.append(str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
