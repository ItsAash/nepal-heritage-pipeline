"""
Neo4j Graph Synchronization Job
"""

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from neo4j import GraphDatabase
from supabase import create_client, ClientOptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import queries

# Constants for edge weighting
EDGE_WEIGHT_ALPHA = 0.7
EDGE_WEIGHT_BETA = 0.3

RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.ConnectTimeout,
    httpx.RemoteProtocolError,
    httpx.ProtocolError,
)

def with_retry():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )

def log_event(event: str, details: Optional[Dict[str, Any]] = None, level: str = "INFO") -> None:
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "level": level,
        **(details or {})
    }
    print(json.dumps(log_entry), file=sys.stderr)

class Neo4jSyncJob:
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        batch_size: int = 500,
    ):
        http_client = httpx.Client(http2=False, timeout=httpx.Timeout(60.0))
        self.supabase = create_client(
            supabase_url,
            supabase_key,
            options=ClientOptions(httpx_client=http_client)
        )
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.batch_size = batch_size

    def close(self):
        self.driver.close()

    def _setup_constraints(self):
        with self.driver.session() as session:
            for q in queries.SETUP_CONSTRAINTS:
                try:
                    session.run(q)
                except Exception as e:
                    log_event("constraint_setup_failed", {"query": q, "error": str(e)}, "WARNING")

    @with_retry()
    def _call_refresh_mvs(self):
        self.supabase.rpc('refresh_neo4j_mvs', {}).execute()

    def run(self, limit: int = 100000):
        log_event("sync_started", {"limit": limit})
        
        self._setup_constraints()

        log_event("refreshing_mvs")
        try:
            self._call_refresh_mvs()
        except Exception as e:
            log_event("mvs_refresh_failed", {"error": str(e)}, "WARNING")

        self._sync_entities(limit)
        self._sync_reviews(limit)
        self._sync_sentiments(limit)

        self._sync_entity_mentions(limit)
        self._sync_sentiment_mentions(limit)
        self._sync_neo4j_edges(limit)

        log_event("sync_completed")
        self.close()

    @with_retry()
    def _get_checkpoint(self, table_name: str):
        res = self.supabase.table("neo4j_sync_checkpoints").select("*").eq("table_name", table_name).execute()
        if res.data:
            return res.data[0]["last_synced_at"], res.data[0]["last_synced_id"]
        return "1970-01-01T00:00:00+00:00", ""

    @with_retry()
    def _update_checkpoint(self, table_name: str, last_synced_at: str, last_synced_id: str):
        self.supabase.table("neo4j_sync_checkpoints").upsert({
            "table_name": table_name,
            "last_synced_at": last_synced_at,
            "last_synced_id": str(last_synced_id),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).execute()

    def reset_checkpoints(self):
        tables = [
            "entities", "cleaned_reviews", "sentiments", 
            "entity_mentions", "sentiment_mentions", "neo4j_edges_mv"
        ]
        for t in tables:
            self.supabase.table("neo4j_sync_checkpoints").upsert({
                "table_name": t,
                "last_synced_at": "1970-01-01T00:00:00+00:00",
                "last_synced_id": ""
            }).execute()
        log_event("checkpoints_reset")

    def _sync_table(self, table_name: str, id_col: str, ts_col: str, limit: int, cypher_query: str, process_batch_fn=None):
        last_synced_at, last_synced_id = self._get_checkpoint(table_name)
        log_event(f"syncing_{table_name}", {"since": last_synced_at, "last_id": last_synced_id})

        processed = 0
        has_more = True

        while has_more and processed < limit:
            batch_limit = min(self.batch_size, limit - processed)
            
            # Robust incremental fetch:
            # If last_synced_id is empty, we just fetch ts > last_synced_at to avoid type casting issues on Postgres.
            if last_synced_id:
                filter_str = f"{ts_col}.gt.{last_synced_at},and({ts_col}.eq.{last_synced_at},{id_col}.gt.{last_synced_id})"
                query = self.supabase.table(table_name).select("*").or_(filter_str)
            else:
                query = self.supabase.table(table_name).select("*").gt(ts_col, last_synced_at)
                
            query = query.order(ts_col, desc=False).order(id_col, desc=False).limit(batch_limit)
            
            try:
                res = query.execute()
                data = res.data
            except Exception as e:
                log_event(f"error_fetching_{table_name}", {"error": str(e)}, "ERROR")
                break
                
            if not data:
                break

            if process_batch_fn:
                data = process_batch_fn(data)

            try:
                with self.driver.session() as session:
                    session.execute_write(self._execute_cypher, cypher_query, data)
            except Exception as e:
                log_event(f"error_writing_neo4j_{table_name}", {"error": str(e)}, "ERROR")
                break

            last_rec = data[-1]
            last_synced_at = last_rec[ts_col]
            last_synced_id = str(last_rec[id_col])

            self._update_checkpoint(table_name, last_synced_at, last_synced_id)
            processed += len(data)
            
            if len(data) < batch_limit:
                has_more = False

        log_event(f"synced_{table_name}", {"count": processed})

    @staticmethod
    def _execute_cypher(tx, query: str, batch: List[Dict[str, Any]]):
        tx.run(query, batch=batch)

    def _sync_entities(self, limit: int):
        self._sync_table("entities", "id", "updated_at", limit, queries.SYNC_ENTITIES)

    def _sync_reviews(self, limit: int):
        self._sync_table("cleaned_reviews", "review_id", "ingested_at", limit, queries.SYNC_REVIEWS)

    def _sync_sentiments(self, limit: int):
        self._sync_table("sentiments", "id", "updated_at", limit, queries.SYNC_SENTIMENTS)

    def _sync_entity_mentions(self, limit: int):
        self._sync_table("entity_mentions", "id", "updated_at", limit, queries.SYNC_ENTITY_MENTIONS)

    def _sync_sentiment_mentions(self, limit: int):
        self._sync_table("sentiment_mentions", "id", "updated_at", limit, queries.SYNC_SENTIMENT_MENTIONS)

    def _sync_neo4j_edges(self, limit: int):
        def calculate_weights(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            for d in data:
                co = d.get("co_occur_count") or 0
                se = d.get("semantic_count") or 0
                d["weight"] = EDGE_WEIGHT_ALPHA * co + EDGE_WEIGHT_BETA * se
            return data

        self._sync_table("neo4j_edges_mv", "id", "updated_at", limit, queries.SYNC_NEO4J_EDGES, process_batch_fn=calculate_weights)
