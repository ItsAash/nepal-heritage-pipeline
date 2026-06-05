# validate_scrape.py
import json
import os
from collections import Counter

OUTPUT_DIR = "raw_reviews"

def validate():
    manifests = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("manifest_")]
    if not manifests:
        print("No manifest found. Run scraper first.")
        return

    with open(f"{OUTPUT_DIR}/{manifests[0]}") as f:
        manifest = json.load(f)

    run_id = manifest["run_id"]
    jsonl_file = manifest["jsonl_file"]

    # Load all reviews
    reviews = []
    with open(jsonl_file, encoding="utf-8") as f:
        for line in f:
            reviews.append(json.loads(line))

    print(f"Run: {run_id}")
    print(f"Total reviews: {len(reviews)}")

    # Checks
    ids = [r["review_id"] for r in reviews]
    print(f"Unique IDs: {len(set(ids))} / {len(ids)} (dups: {len(ids) - len(set(ids))})")

    langs = Counter(r.get("language") for r in reviews)
    print(f"Languages: {dict(langs)}")

    ratings = Counter(r.get("rating") for r in reviews)
    print(f"Ratings: {dict(sorted(ratings.items()))}")

    dates = [r.get("published_at_date") for r in reviews if r.get("published_at_date")]
    print(f"Date range: {min(dates)} to {max(dates)}")

    missing_text = sum(1 for r in reviews if not r.get("text"))
    print(f"Missing text: {missing_text}")

    print("\n✓ Validation complete")

if __name__ == "__main__":
    validate()