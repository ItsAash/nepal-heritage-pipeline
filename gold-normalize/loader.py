"""
loader.py
Resilient, batch-based Supabase orchestration for Gold Canonical normalization.
"""

import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import httpx
from supabase import create_client, ClientOptions
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from normalizer import (
    EntityResolver,
    normalize_aspect,
    normalize_label,
    normalize_sentiment_label,
    relation_endpoint_from_review_entities,
)

# ════════════════════════════════════════════════════════════════
# Configuration & Resilience
# ════════════════════════════════════════════════════════════════

RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.ConnectTimeout,
    httpx.RemoteProtocolError,
    httpx.ProtocolError,
)

def with_retry():
    """Retry decorator for Supabase API calls."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )

def log_event(event: str, details: Optional[Dict[str, Any]] = None, level: str = "INFO") -> None:
    """Structured JSON logging to stderr."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "level": level,
        **(details or {})
    }
    print(json.dumps(log_entry), file=sys.stderr)

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

# ════════════════════════════════════════════════════════════════
# CanonicalLoader Implementation
# ════════════════════════════════════════════════════════════════

class CanonicalLoader:
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        page_size: int = 100,
        auto_alias_threshold: int = 95,
        candidate_alias_threshold: int = 75,
        timeout: float = 30.0,
    ):
        # Configure httpx client: Disable HTTP/2 for stability, set strict timeouts
        http_client = httpx.Client(
            http2=False, 
            timeout=httpx.Timeout(
                connect=10.0, read=timeout, write=timeout, pool=60.0
            )
        )
        
        self.supabase = create_client(
            supabase_url, 
            supabase_key,
            options=ClientOptions(httpx_client=http_client)
        )
        self.page_size = page_size
        self.resolver = EntityResolver(
            auto_threshold=auto_alias_threshold,
            candidate_threshold=candidate_alias_threshold,
        )
        
        # In-memory caches for lightning-fast resolution (No API calls during loop)
        self.entity_id_cache: Dict[tuple[str, str], int] = {}
        self.entities_by_id: Dict[int, Dict[str, Any]] = {}
        self.sentiment_id_cache: Dict[str, int] = {}
        self.relation_id_cache: Dict[tuple[int, int, str], int] = {}
        
    def run(self, limit: Optional[int] = None, include_processed: bool = False) -> Dict[str, int]:
        run_id = self.start_run()
        counts = {"entities": 0, "relations": 0, "sentiments": 0}
        
        try:
            # 1. Warm up local caches (Bulk fetch)
            log_event("loading_caches", {"step": "entities"})
            existing_entities = self.fetch_all("entities", "id,canonical_name,display_name,entity_type")
            self.load_existing_entities(existing_entities)
            
            log_event("loading_caches", {"step": "aliases"})
            self.load_existing_aliases()
            
            log_event("loading_caches", {"step": "sentiments"})
            self.load_existing_sentiments()
            
            log_event("loading_caches", {"step": "checkpoints"})
            checkpoints = self.fetch_processed_checkpoint_ids() if not include_processed else defaultdict(set)
            
            log_event("loading_caches", {"step": "reviews"})
            reviews_by_id = self.fetch_reviews_by_id()
            
            # 2. Process Tables sequentially
            # Process Entities
            raw_entities = self.pending_rows("entities_raw", checkpoints, limit)
            if raw_entities:
                log_event("processing_entities_start", {"count": len(raw_entities)})
                e_count = self.process_batch("entities_raw", raw_entities, run_id)
                counts["entities"] = e_count
                log_event("processing_entities_complete", {"processed": e_count})

            # Process Relations
            raw_relations = self.pending_rows("relations_raw", checkpoints, limit)
            if raw_relations:
                log_event("processing_relations_start", {"count": len(raw_relations)})
                # We need the current state of entities in raw format for resolution
                entity_rows_by_review = self.group_by_review(self.fetch_all("entities_raw", "*"))
                r_count = self.process_batch("relations_raw", raw_relations, run_id, 
                                            extra_context={"entities_by_review": entity_rows_by_review, "reviews_by_id": reviews_by_id})
                counts["relations"] = r_count
                log_event("processing_relations_complete", {"processed": r_count})

            # Process Sentiments
            raw_sentiments = self.pending_rows("sentiments_raw", checkpoints, limit)
            if raw_sentiments:
                log_event("processing_sentiments_start", {"count": len(raw_sentiments)})
                s_count = self.process_batch("sentiments_raw", raw_sentiments, run_id, 
                                            extra_context={"reviews_by_id": reviews_by_id})
                counts["sentiments"] = s_count
                log_event("processing_sentiments_complete", {"processed": s_count})

            # 3. Finalize
            self.supabase.rpc("refresh_canonical_aggregates").execute()
            self.finish_run(run_id, "completed", counts)
            log_event("normalization_complete", {"run_id": run_id, **counts})
            return counts
            
        except Exception as exc:
            self.finish_run(run_id, "failed", counts, str(exc))
            log_event("normalization_critical_failure", {"error": str(exc)}, "ERROR")
            raise

    def process_batch(self, table: str, rows: List[Dict[str, Any]], run_id: int, extra_context: Dict = None) -> int:
        """
        Processes a list of rows in memory and performs bulk upserts.
        """
        processed_count = 0
        batch_size = 100
        
        # Result buffers for bulk upload
        upserts = defaultdict(list) # table_name -> [records]
        checkpoints = [] # [ {raw_table, raw_id, status, ...} ]
        
        for i, row in enumerate(rows, start=1):
            try:
                if table == "entities_raw":
                    res = self._process_entity_logic(row)
                elif table == "relations_raw":
                    res = self._process_relation_logic(row, extra_context["entities_by_review"], extra_context["reviews_by_id"])
                else: # sentiments_raw
                    res = self._process_sentiment_logic(row, extra_context["reviews_by_id"])
                
                # Add results to buffers
                for tbl, records in res.items():
                    upserts[tbl].extend(records)
                
                checkpoints.append({
                    "raw_table": table,
                    "raw_id": row["id"],
                    "run_id": run_id,
                    "status": "processed",
                    "updated_at": utc_now(),
                })
                processed_count += 1
                
            except Exception as exc:
                # Mark individual row as failed, but keep processing the batch
                self.mark_checkpoint(table, row["id"], run_id, "failed", str(exc))
                log_event(f"{table}_row_failed", {"raw_id": row.get("id"), "error": str(exc)}, "ERROR")

            # Flush buffers periodically to avoid huge payloads
            if i % batch_size == 0:
                self.flush_buffers(upserts, checkpoints)
                upserts.clear()
                checkpoints.clear()
                log_event("batch_flushed", {"processed": i, "table": table})

        # Final flush
        self.flush_buffers(upserts, checkpoints)
        return processed_count

    def flush_buffers(self, upserts: Dict[str, List[Dict]], checkpoints: List[Dict]) -> None:
        """Performs bulk upserts to Supabase with retries."""
        # 1. Upsert actual data
        for table, records in upserts.items():
            if not records: continue
            try:
                # We use .insert() or .upsert(). For canonical tables, we use upsert on unique keys.
                # Note: Supabase .upsert() requires the 'on_conflict' parameter.
                on_conflict = {
                    "entities": "canonical_name,entity_type",
                    "entity_aliases": "normalized_alias,entity_type,scope_type,scope_id",
                    "relations": "source_entity_id,target_entity_id,relation_type",
                    "sentiments": "aspect",
                }.get(table, "id")
                
                self._safe_execute(
                    lambda: self.supabase.table(table).upsert(records, on_conflict=on_conflict).execute()
                )
            except Exception as e:
                log_event("batch_upsert_failed", {"table": table, "count": len(records), "error": str(e)}, "ERROR")
                raise

        # 2. Upsert checkpoints
        if checkpoints:
            self._safe_execute(
                lambda: self.supabase.table("normalization_checkpoints").upsert(checkpoints, on_conflict="raw_table,raw_id").execute()
            )

    def _safe_execute(self, func):
        """Wrapper for retries."""
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
        
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            reraise=True,
        )
        def execute():
            return func()
        return execute()

    # ════════════════════════════════════════════════════════════════
    # Logic Methods (In-Memory)
    # ════════════════════════════════════════════════════════════════

    def _process_entity_logic(self, row: Dict[str, Any]) -> Dict[str, List[Dict]]:
        results = defaultdict(list)
        
        entity_id, aliases = self.ensure_entity_with_alias(
            row.get("entity_name"),
            row.get("entity_type"),
            raw_entity_id=row.get("id"),
        )
        if aliases:
            results["entity_aliases"].extend(aliases)
        
        # Mention record
        results["entity_mentions"].append({
            "raw_entity_id": row["id"],
            "entity_id": entity_id,
            "review_id": row["review_id"],
            "entity_name_raw": row.get("entity_name") or "",
            "normalized_alias": normalize_label(row.get("entity_name")),
            "entity_type_raw": row.get("entity_type") or "unknown",
            "quote": row.get("quote"),
            "updated_at": utc_now(),
        })
        return results

    def _process_relation_logic(self, row: Dict[str, Any], entity_rows_by_review: Dict, reviews_by_id: Dict) -> Dict[str, List[Dict]]:
        results = defaultdict(list)
        review_entities = entity_rows_by_review.get(row["review_id"], [])
        source = relation_endpoint_from_review_entities(row.get("source_node"), review_entities)
        target = relation_endpoint_from_review_entities(row.get("target_node"), review_entities)

        source_entity_id, src_al = self.ensure_entity_with_alias(source.get("entity_name"), source.get("entity_type"))
        target_entity_id, tgt_al = self.ensure_entity_with_alias(target.get("entity_name"), target.get("entity_type"))
        
        if src_al: results["entity_aliases"].extend(src_al)
        if tgt_al: results["entity_aliases"].extend(tgt_al)
        
        relation_id = self.ensure_relation(source_entity_id, target_entity_id, row.get("relation"))

        results["relation_mentions"].append({
            "raw_relation_id": row["id"],
            "relation_id": relation_id,
            "review_id": row["review_id"],
            "source_node_raw": row.get("source_node") or "",
            "target_node_raw": row.get("target_node") or "",
            "relation_type_raw": row.get("relation") or "unknown",
            "description": row.get("description"),
            "updated_at": utc_now(),
        })
        return results

    def _process_sentiment_logic(self, row: Dict[str, Any], reviews_by_id: Dict) -> Dict[str, List[Dict]]:
        results = defaultdict(list)
        resolved = normalize_aspect(row.get("aspect"))
        sentiment_id = self.ensure_sentiment(resolved.aspect, resolved.display_aspect)

        results["sentiment_mentions"].append({
            "raw_sentiment_id": row["id"],
            "sentiment_id": sentiment_id,
            "review_id": row["review_id"],
            "aspect_raw": row.get("aspect") or "",
            "sentiment_label": normalize_sentiment_label(row.get("sentiment")),
            "sentiment_score": row.get("score") if row.get("score") is not None else 0.5,
            "evidence": row.get("evidence"),
            "updated_at": utc_now(),
        })
        return results

    # ════════════════════════════════════════════════════════════════
    # Cache-First Helpers
    # ════════════════════════════════════════════════════════════════

    def ensure_entity_with_alias(self, raw_name: Any, entity_type: Any, raw_entity_id: Optional[int] = None) -> Tuple[int, List[Dict]]:
        resolved = self.resolver.resolve(raw_name, entity_type)
        cache_key = (resolved.canonical_name, resolved.entity_type)
        
        if cache_key in self.entity_id_cache:
            entity_id = self.entity_id_cache[cache_key]
        else:
            self.upsert("entities", {
                "canonical_name": resolved.canonical_name,
                "display_name": resolved.display_name,
                "entity_type": resolved.entity_type,
                "updated_at": utc_now(),
            }, "canonical_name,entity_type")
            
            entity = self.select_one("entities", "id,canonical_name,display_name,entity_type", {
                "canonical_name": resolved.canonical_name,
                "entity_type": resolved.entity_type,
            })
            
            self.entity_id_cache[cache_key] = entity["id"]
            self.entities_by_id[entity["id"]] = entity
            entity_id = entity["id"]

        aliases = []
        if resolved.matched_by != "learned_alias" and resolved.raw_normalized_alias:
            source = {
                "learned_alias": "exact", "exact": "exact", "fuzzy": "fuzzy_auto",
                "token_subset": "token_subset_auto", "new": "exact", "empty": "exact",
                "fuzzy_candidate": "exact", "token_subset_candidate": "exact",
            }.get(resolved.matched_by, "auto")

            status = "pending" if resolved.is_candidate else "approved"
            suggested_id = None
            if resolved.suggested_canonical_name:
                suggested_key = (resolved.suggested_canonical_name, resolved.entity_type)
                suggested_id = self.entity_id_cache.get(suggested_key)

            aliases.append({
                "entity_id": entity_id,
                "normalized_alias": resolved.raw_normalized_alias,
                "display_alias": str(raw_name or "").strip() or resolved.display_name,
                "entity_type": resolved.entity_type,
                "source": source,
                "confidence": resolved.confidence,
                "status": status,
                "match_method": resolved.matched_by,
                "suggested_merge_entity_id": suggested_id,
                "scope_type": "global",
                "scope_id": "global",
                "first_seen_raw_id": raw_entity_id,
                "last_seen_raw_id": raw_entity_id,
                "updated_at": utc_now(),
            })

            self.resolver.add_alias(
                resolved.raw_normalized_alias,
                resolved.canonical_name,
                resolved.display_name,
                resolved.entity_type,
                entity_id,
                resolved.confidence,
            )

        return entity_id, aliases

    def ensure_relation(self, source_id: int, target_id: int, rel_type: Any) -> int:
        norm_type = str(rel_type or "unknown").strip().lower() or "unknown"
        cache_key = (source_id, target_id, norm_type)
        if cache_key in self.relation_id_cache:
            return self.relation_id_cache[cache_key]
        
        self.upsert("relations", {
            "source_entity_id": source_id,
            "target_entity_id": target_id,
            "relation_type": norm_type,
            "updated_at": utc_now(),
        }, "source_entity_id,target_entity_id,relation_type")
        
        rel = self.select_one("relations", "id", {
            "source_entity_id": source_id,
            "target_entity_id": target_id,
            "relation_type": norm_type,
        })
        self.relation_id_cache[cache_key] = rel["id"]
        return rel["id"]

    def ensure_sentiment(self, aspect: str, display_aspect: str) -> int:
        if aspect in self.sentiment_id_cache:
            return self.sentiment_id_cache[aspect]
        
        self.upsert("sentiments", {
            "aspect": aspect,
            "display_aspect": display_aspect,
            "updated_at": utc_now(),
        }, "aspect")
        
        sent = self.select_one("sentiments", "id", {"aspect": aspect})
        self.sentiment_id_cache[aspect] = sent["id"]
        return sent["id"]

    def upsert(self, table: str, record: Dict[str, Any], on_conflict: str) -> None:
        self._safe_execute(lambda: self.supabase.table(table).upsert(record, on_conflict=on_conflict).execute())

    def select_one(self, table: str, select: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        def _do():
            query = self.supabase.table(table).select(select)
            for col, val in filters.items():
                query = query.eq(col, val)
            res = query.limit(1).execute()
            if not res.data:
                raise LookupError(f"{table} not found")
            return res.data[0]
        return self._safe_execute(_do)

    def fetch_all(self, table: str, select: str) -> List[Dict[str, Any]]:
        rows = []
        offset = 0
        while True:
            res = self._safe_execute(
                lambda: self.supabase.table(table).select(select).range(offset, offset + self.page_size - 1).execute()
            )
            page = res.data or []
            rows.extend(page)
            if len(page) < self.page_size: break
            offset += self.page_size
        return rows

    def load_existing_entities(self, entities: Iterable[Dict[str, Any]]) -> None:
        for e in entities:
            t = e.get("entity_type") or "unknown"
            self.entity_id_cache[(e["canonical_name"], t)] = e["id"]
            self.entities_by_id[e["id"]] = e

    def load_existing_aliases(self) -> None:
        aliases = self.fetch_all("entity_aliases", "entity_id,normalized_alias,entity_type,confidence")
        for a in aliases:
            e = self.entities_by_id.get(a["entity_id"])
            if e:
                self.resolver.add_alias(a["normalized_alias"], e["canonical_name"], e["display_name"], a["entity_type"], a["entity_id"], float(a["confidence"]))

    def load_existing_sentiments(self) -> None:
        sents = self.fetch_all("sentiments", "id,aspect")
        for s in sents:
            self.sentiment_id_cache[s["aspect"]] = s["id"]

    def fetch_processed_checkpoint_ids(self) -> Dict[str, Set[int]]:
        checkpoints = defaultdict(set)
        rows = self.fetch_all("normalization_checkpoints", "raw_table,raw_id,status")
        for r in rows:
            if r.get("status") == "processed":
                checkpoints[r["raw_table"]].add(r["raw_id"])
        return checkpoints

    def pending_rows(self, table: str, checkpoints: Dict[str, Set[int]], limit: Optional[int]) -> List[Dict[str, Any]]:
        rows = [r for r in self.fetch_all(table, "*") if r.get("id") not in checkpoints.get(table, set())]
        return rows[:limit] if limit else rows

    def fetch_reviews_by_id(self) -> Dict[str, Dict[str, Any]]:
        rows = self.fetch_all("cleaned_reviews", "review_id,year,period,trip_type,rating")
        return {r["review_id"]: r for r in rows}

    def group_by_review(self, rows: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped = defaultdict(list)
        for r in rows: grouped[r["review_id"]].append(r)
        return grouped

    def start_run(self) -> int:
        res = self.supabase.table("normalization_runs").insert({"status": "running"}).execute()
        return res.data[0]["id"]

    def finish_run(self, run_id: int, status: str, counts: Dict[str, int], error: Optional[str] = None) -> None:
        self.supabase.table("normalization_runs").update({
            "status": status, "finished_at": utc_now(),
            "entities_processed": counts["entities"],
            "relations_processed": counts["relations"],
            "sentiments_processed": counts["sentiments"],
            "error_message": error, "updated_at": utc_now()
        }).eq("id", run_id).execute()

    def mark_checkpoint(self, table: str, raw_id: int, run_id: int, status: str, error: Optional[str] = None) -> None:
        self.upsert("normalization_checkpoints", {
            "raw_table": table, "raw_id": raw_id, "run_id": run_id,
            "status": status, "error_message": error[:500] if error else None, "updated_at": utc_now()
        }, "raw_table,raw_id")

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def log_event(event: str, details: Optional[Dict[str, Any]] = None, level: str = "INFO") -> None:
    print(json.dumps({"event": event, "level": level, **(details or {})}), file=sys.stderr)
