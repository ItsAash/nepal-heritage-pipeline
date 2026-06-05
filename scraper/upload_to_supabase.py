# scraper/upload_to_supabase.py
import os
import json
from pathlib import Path
from datetime import datetime

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def upload_run():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    run_date = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Find JSONL file
    jsonl_files = list(Path("raw_reviews").glob("reviews_*.jsonl"))
    if not jsonl_files:
        raise Exception("No JSONL file found in raw_reviews/")

    jsonl_file = jsonl_files[0]
    print(f"Uploading {jsonl_file.name} to Supabase Storage...")

    # Upload raw JSONL to Supabase Storage bucket
    with open(jsonl_file, "rb") as f:
        file_content = f.read()

    storage_path = f"tripadvisor/run_{run_date}/{jsonl_file.name}"

    # Create bucket if not exists (or use existing)
    try:
        supabase.storage.create_bucket("raw-reviews", options={"public": False})
    except Exception:
        pass  # Bucket likely exists

    # Upload file
    result = supabase.storage.from_("raw-reviews").upload(
        path=storage_path,
        file=file_content,
        file_options={"content-type": "application/jsonl"}
    )

    print(f"✓ Uploaded to Storage: {storage_path}")

    # Also insert metadata into a table for tracking
    manifest_files = list(Path("raw_reviews").glob("manifest_*.json"))
    if manifest_files:
        with open(manifest_files[0]) as f:
            manifest = json.load(f)

        # Insert into tracking table
        data = {
            "run_id": manifest["run_id"],
            "run_date": run_date,
            "total_reviews": manifest["total_reviews"],
            "total_pages": manifest["total_pages"],
            "storage_path": storage_path,
            "scraped_at": manifest["scraped_at"]
        }

        supabase.table("scrape_runs").insert(data).execute()
        print(f"✓ Logged run metadata to scrape_runs table")

if __name__ == "__main__":
    upload_run()