"""
Standalone Neo4j Graph Synchronization workflow.
"""

import argparse
import os
import sys
import dotenv
from sync_job import Neo4jSyncJob

def parse_args():
    parser = argparse.ArgumentParser(description="Synchronize Canonical Gold tables to Neo4j Aura.")
    parser.add_argument(
        "--limit",
        type=int,
        default=100000,
        help="Maximum raw rows per table to process in this run."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of records to MERGE per transaction."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset all checkpoints and sync from scratch."
    )
    return parser.parse_args()

def main() -> int:
    dotenv.load_dotenv()
    args = parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not all([supabase_url, supabase_key, neo4j_uri, neo4j_user, neo4j_password]):
        raise ValueError("Missing required environment variables for Supabase or Neo4j.")

    job = Neo4jSyncJob(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        batch_size=args.batch_size
    )
    
    if args.reset:
        job.reset_checkpoints()
        
    job.run(limit=args.limit)
    return 0

if __name__ == "__main__":
    sys.exit(main())
