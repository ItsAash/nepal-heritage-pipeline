"""
Standalone Gold Canonical normalization workflow.

This job reads existing staging tables in Supabase:
  - entities_raw
  - relations_raw
  - sentiments_raw

It writes canonical tables and mention tables without mutating raw tables.
"""

import argparse
import os

import dotenv

from loader import CanonicalLoader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Gold staging rows into canonical Gold tables.")
    parser.add_argument(
        "--limit",
        type=int,
        default=os.getenv("MAX_ROWS_PER_RUN"),
        help="Maximum raw rows per staging table to process in this run.",
    )
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="Reprocess rows already present in normalization_checkpoints. Mention upserts keep this idempotent.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=int(os.getenv("NORMALIZATION_PAGE_SIZE", "1000")),
        help="Supabase page size for table scans.",
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

    limit = int(args.limit) if args.limit is not None else None
    loader = CanonicalLoader(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        page_size=args.page_size,
        auto_alias_threshold=args.auto_alias_threshold,
        candidate_alias_threshold=args.candidate_alias_threshold,
    )
    loader.run(limit=limit, include_processed=args.include_processed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
