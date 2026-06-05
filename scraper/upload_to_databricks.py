# scraper/upload_to_databricks.py
import os
import requests
import json
from pathlib import Path
from datetime import datetime

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "").rstrip("/")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
VOLUME_PATH = "/Volumes/workspace/default/raw_tripadvisor_reviews"

def upload_file(local_path, remote_path):
    """Upload a file to Databricks Unity Catalog Volume using REST API"""
    url = f"{DATABRICKS_HOST}/api/2.0/fs/files{remote_path}"

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}"
    }

    with open(local_path, "rb") as f:
        response = requests.put(url, headers=headers, data=f)

    # 200, 201, 204 are all success codes for Databricks file upload
    if response.status_code not in [200, 201, 204]:
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")

    print(f"✓ Uploaded {local_path} → {remote_path}")

def create_directory(remote_dir):
    """Create directory by uploading empty file then deleting it"""
    temp_file = "/tmp/.dir_placeholder"
    with open(temp_file, "w") as f:
        f.write("")

    url = f"{DATABRICKS_HOST}/api/2.0/fs/files{remote_dir}/.placeholder"
    headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}

    with open(temp_file, "rb") as f:
        response = requests.put(url, headers=headers, data=f)

    # 204 is success (no content)
    if response.status_code in [200, 201, 204]:
        # Delete the placeholder
        requests.delete(url, headers=headers)
        print(f"✓ Created directory: {remote_dir}")
    else:
        print(f"Warning: Could not create directory {remote_dir}: {response.status_code}")

def upload_run():
    run_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_path = f"{VOLUME_PATH}/run_{run_date}"

    print(f"Uploading to {run_path}")

    # Create run directory
    create_directory(run_path)

    # Create pages subdirectory
    pages_path = f"{run_path}/pages"
    create_directory(pages_path)

    # Upload JSONL
    for jsonl_file in Path("raw_reviews").glob("reviews_*.jsonl"):
        upload_file(str(jsonl_file), f"{run_path}/{jsonl_file.name}")

    # Upload manifest
    for manifest_file in Path("raw_reviews").glob("manifest_*.json"):
        upload_file(str(manifest_file), f"{run_path}/{manifest_file.name}")

    # Upload page files
    for page_file in Path("raw_reviews").glob("page_*.json"):
        upload_file(str(page_file), f"{pages_path}/{page_file.name}")

    print(f"✓ Upload complete: {run_path}")

if __name__ == "__main__":
    upload_run()