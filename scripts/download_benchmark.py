import os
import json
import requests
from pathlib import Path
import sys

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

def download_file(url: str, dest: Path) -> bool:
    """Downloads a file from url to dest with a simulated browser User-Agent."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        # Some URLs are http, try to handle ssl errors
        response = requests.get(url, headers=headers, stream=True, timeout=30, verify=False)
        if response.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        else:
            print(f"  [ERROR] HTTP status {response.status_code} for {url}")
            return False
    except Exception as e:
        print(f"  [ERROR] Connection error for {url}: {e}")
        return False

def main():
    metadata_path = config.BENCHMARK_DIR / "metadata.json"
    if not metadata_path.exists():
        print("[CRITICAL] data/benchmark/metadata.json not found!")
        return

    with open(metadata_path, "r") as f:
        documents = json.load(f)

    print("==================================================")
    print(" PolicyLens Corpus Sync Utility")
    print("==================================================")
    print(f"Target Directory: {config.BENCHMARK_DIR}\n")

    results = []
    
    for doc in documents:
        doc_id = doc["document_id"]
        title = doc["title"]
        url = doc["source_url"]
        filename = doc["filename"]
        dest_path = config.BENCHMARK_DIR / filename

        print(f"[*] Processing: {title}")
        if dest_path.exists():
            size_mb = dest_path.stat().st_size / (1024 * 1024)
            print(f"  [ALREADY EXISTS] {filename} ({size_mb:.2f} MB). Skipping download.")
            results.append((title, "Success (Cached)", filename))
        else:
            print(f"  [DOWNLOADING] From: {url} ...")
            success = download_file(url, dest_path)
            if success:
                size_mb = dest_path.stat().st_size / (1024 * 1024)
                print(f"  [SUCCESS] Saved as {filename} ({size_mb:.2f} MB)")
                results.append((title, "Success (Downloaded)", filename))
            else:
                print(f"  [FAILED] Could not download official PDF.")
                results.append((title, "Failed", filename))

    print("\n==================================================")
    print(" Sync Status Summary")
    print("==================================================")
    for title, status, filename in results:
        indicator = "[OK]" if "Success" in status else "[FAIL]"
        print(f"{indicator} {title:<55} : {status}")

    failed_docs = [r for r in results if r[1] == "Failed"]
    if failed_docs:
        print("\n==================================================")
        print(" ACTION REQUIRED: Manual PDF Supply Instructions")
        print("==================================================")
        print("Some official files could not be downloaded automatically.")
        print("Please manually download them and place them in the corpus directory:")
        print(f"Path: {config.BENCHMARK_DIR}\n")
        
        for doc in documents:
            filename = doc["filename"]
            if any(f[2] == filename for f in failed_docs):
                print(f"- {doc['title']}")
                print(f"  Expected Filename: {filename}")
                print(f"  Official Source Link: {doc['source_url']}")
                print()
    else:
        print("\n[SUCCESS] All benchmark files are available!")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
