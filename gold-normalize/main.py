"""
Standalone Gold Canonical normalization workflow.
"""

import argparse
import os
import dotenv
from loader import CanonicalLoader

def parse_args():
    parser = argparse.ArgumentParser(description="Normalize Gold staging rows into canonical Gold tables.")
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.getenv("MAX_ROWS_PER_RUN", "1000000")),
        help="Maximum raw rows per staging table to process in this run.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("NORMALIZATION_BATCH_SIZE", "100")),
        help="Number of records to process before flushing to database.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=int(os.getenv("NORMALIZATION_PAGE_SIZE", "100")),
        help="Supabase page size for table scans.",
    )
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="Reprocess rows already present in normalization_checkpoints.",
    )
    parser.add_argument(
        "--auto-alias-threshold",
        type=int,
        default=int(os.getenv("AUTO_ALIAS_THRESHOLD", "95")),
        help="RapidFuzz token-sort threshold for auto-approving a learned alias.",
    )
    parser.add_argument(
        "--candidate-alias-threshold",
        type=int,
        default=int(os.getenv("CANDIDATE_ALIAS_THRESHOLD", "75")),
        help="RapidFuzz token-sort threshold for creating an alias review candidate.",
    )
    return parser.parse_args()

def main() -> int:
    dotenv.load_dotenv()
    args = parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Missing required env vars: SUPABASE_URL, SUPABASE_KEY")

    loader = CanonicalLoader(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        page_size=args.page_size,
        auto_alias_threshold=args.auto_alias_threshold,
        candidate_alias_threshold=args.candidate_alias_threshold,
    )
    
    # Set the batch size for processing
    loader.batch_size = args.batch_size
    
    loader.run(limit=args.limit, include_processed=args.include_processed)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
