"""
Supabase orchestration for the standalone Gold Canonical workflow.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

from supabase import create_client

from normalizer import (
    EntityResolver,
    normalize_aspect,
    normalize_label,
    normalize_sentiment_label,
    relation_endpoint_from_review_entities,
)


RAW_TABLES = {
    "entities_raw": "raw_entity_id",
    "relations_raw": "raw_relation_id",
    "sentiments_raw": "raw_sentiment_id",
}


class CanonicalLoader:
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        page_size: int = 1000,
        auto_alias_threshold: int = 95,
        candidate_alias_threshold: int = 75,
    ):
        self.supabase = create_client(supabase_url, supabase_key)
        self.page_size = page_size
        self.resolver = EntityResolver(
            auto_threshold=auto_alias_threshold,
            candidate_threshold=candidate_alias_threshold,
        )
        self.entity_id_cache: Dict[tuple[str, str], int] = {}
        self.entities_by_id: Dict[int, Dict[str, Any]] = {}
        self.sentiment_id_cache: Dict[str, int] = {}
        self.relation_id_cache: Dict[tuple[int, int, str], int] = {}

    def run(self, limit: Optional[int] = None, include_processed: bool = False) -> Dict[str, int]:
        run_id = self.start_run()
        counts = {"entities": 0, "relations": 0, "sentiments": 0}

        try:
            existing_entities = self.fetch_all("entities", "id,canonical_name,display_name,entity_type")
            self.load_existing_entities(existing_entities)
            self.promote_approved_alias_candidates()
            self.load_existing_aliases()
            checkpoints = self.fetch_processed_checkpoint_ids() if not include_processed else defaultdict(set)
            reviews_by_id = self.fetch_reviews_by_id()

            raw_entities = self.pending_rows("entities_raw", checkpoints, limit)
            entity_rows_by_review = self.group_by_review(self.fetch_all("entities_raw", "*"))

            for row in raw_entities:
                try:
                    self.process_entity(row)
                    self.mark_checkpoint("entities_raw", row["id"], run_id, "processed")
                    counts["entities"] += 1
                except Exception as exc:
                    self.mark_checkpoint("entities_raw", row["id"], run_id, "failed", str(exc))
                    log_event("entity_normalization_failed", {"raw_id": row.get("id"), "error": str(exc)}, "ERROR")

            raw_relations = self.pending_rows("relations_raw", checkpoints, limit)
            for row in raw_relations:
                try:
                    self.process_relation(row, entity_rows_by_review, reviews_by_id)
                    self.mark_checkpoint("relations_raw", row["id"], run_id, "processed")
                    counts["relations"] += 1
                except Exception as exc:
                    self.mark_checkpoint("relations_raw", row["id"], run_id, "failed", str(exc))
                    log_event("relation_normalization_failed", {"raw_id": row.get("id"), "error": str(exc)}, "ERROR")

            raw_sentiments = self.pending_rows("sentiments_raw", checkpoints, limit)
            for row in raw_sentiments:
                try:
                    self.process_sentiment(row, reviews_by_id)
                    self.mark_checkpoint("sentiments_raw", row["id"], run_id, "processed")
                    counts["sentiments"] += 1
                except Exception as exc:
                    self.mark_checkpoint("sentiments_raw", row["id"], run_id, "failed", str(exc))
                    log_event("sentiment_normalization_failed", {"raw_id": row.get("id"), "error": str(exc)}, "ERROR")

            self.supabase.rpc("refresh_canonical_aggregates").execute()
            self.finish_run(run_id, "completed", counts)
            log_event("normalization_complete", {"run_id": run_id, **counts})
            return counts
        except Exception as exc:
            self.finish_run(run_id, "failed", counts, str(exc))
            raise

    def fetch_all(self, table: str, select: str) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        offset = 0
        while True:
            response = (
                self.supabase.table(table)
                .select(select)
                .range(offset, offset + self.page_size - 1)
                .execute()
            )
            page = response.data or []
            rows.extend(page)
            if len(page) < self.page_size:
                break
            offset += self.page_size
        return rows

    def load_existing_entities(self, entities: Iterable[Dict[str, Any]]) -> None:
        for entity in entities:
            entity_type = entity.get("entity_type") or "unknown"
            cache_key = (entity["canonical_name"], entity_type)
            self.entity_id_cache[cache_key] = entity["id"]
            self.entities_by_id[entity["id"]] = entity
            self.resolver.add_existing(
                entity["canonical_name"],
                entity["display_name"],
                entity_type,
                entity["id"],
            )

    def load_existing_aliases(self) -> None:
        aliases = self.fetch_all("entity_aliases", "entity_id,normalized_alias,entity_type,confidence")
        for alias in aliases:
            entity = self.entities_by_id.get(alias["entity_id"])
            if not entity:
                continue
            self.resolver.add_alias(
                alias["normalized_alias"],
                entity["canonical_name"],
                entity["display_name"],
                alias.get("entity_type") or entity.get("entity_type") or "unknown",
                alias["entity_id"],
                float(alias.get("confidence") or 1.0),
            )

    def promote_approved_alias_candidates(self) -> None:
        candidates = [
            row for row in self.fetch_all(
                "entity_alias_candidates",
                "normalized_alias,display_alias,suggested_entity_id,entity_type,confidence,scope_type,scope_id,status",
            )
            if row.get("status") == "approved"
        ]

        for candidate in candidates:
            self.upsert(
                "entity_aliases",
                {
                    "entity_id": candidate["suggested_entity_id"],
                    "normalized_alias": candidate["normalized_alias"],
                    "display_alias": candidate["display_alias"],
                    "entity_type": candidate["entity_type"],
                    "source": "manual",
                    "confidence": candidate.get("confidence") or 1.0,
                    "scope_type": candidate.get("scope_type") or "global",
                    "scope_id": candidate.get("scope_id") or "global",
                    "updated_at": utc_now(),
                },
                "normalized_alias,entity_type,scope_type,scope_id",
            )

    def fetch_processed_checkpoint_ids(self) -> Dict[str, Set[int]]:
        checkpoints = defaultdict(set)
        rows = self.fetch_all("normalization_checkpoints", "raw_table,raw_id,status")
        for row in rows:
            if row.get("status") == "processed":
                checkpoints[row["raw_table"]].add(row["raw_id"])
        return checkpoints

    def pending_rows(
        self,
        table: str,
        checkpoints: Dict[str, Set[int]],
        limit: Optional[int],
    ) -> List[Dict[str, Any]]:
        rows = [
            row for row in self.fetch_all(table, "*")
            if row.get("id") not in checkpoints.get(table, set())
        ]
        if limit is not None:
            return rows[:limit]
        return rows

    def fetch_reviews_by_id(self) -> Dict[str, Dict[str, Any]]:
        rows = self.fetch_all("cleaned_reviews", "review_id,year,period,trip_type,rating")
        return {row["review_id"]: row for row in rows}

    def group_by_review(self, rows: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["review_id"]].append(row)
        return grouped

    def process_entity(self, row: Dict[str, Any]) -> None:
        entity_id = self.ensure_entity(
            row.get("entity_name"),
            row.get("entity_type"),
            raw_entity_id=row.get("id"),
            review_id=row.get("review_id"),
        )
        self.upsert(
            "entity_mentions",
            {
                "raw_entity_id": row["id"],
                "entity_id": entity_id,
                "review_id": row["review_id"],
                "year": row.get("year"),
                "period": row.get("period"),
                "trip_type": row.get("trip_type"),
                "rating": row.get("rating"),
                "entity_name_raw": row.get("entity_name") or "",
                "normalized_alias": normalize_label(row.get("entity_name")),
                "entity_type_raw": row.get("entity_type") or "unknown",
                "quote": row.get("quote"),
                "updated_at": utc_now(),
            },
            "raw_entity_id",
        )

    def process_relation(
        self,
        row: Dict[str, Any],
        entity_rows_by_review: Dict[str, List[Dict[str, Any]]],
        reviews_by_id: Dict[str, Dict[str, Any]],
    ) -> None:
        review_entities = entity_rows_by_review.get(row["review_id"], [])
        source = relation_endpoint_from_review_entities(row.get("source_node"), review_entities)
        target = relation_endpoint_from_review_entities(row.get("target_node"), review_entities)

        source_entity_id = self.ensure_entity(
            source.get("entity_name"),
            source.get("entity_type"),
            review_id=row.get("review_id"),
        )
        target_entity_id = self.ensure_entity(
            target.get("entity_name"),
            target.get("entity_type"),
            review_id=row.get("review_id"),
        )
        relation_id = self.ensure_relation(source_entity_id, target_entity_id, row.get("relation"))
        review = reviews_by_id.get(row["review_id"], {})

        self.upsert(
            "relation_mentions",
            {
                "raw_relation_id": row["id"],
                "relation_id": relation_id,
                "review_id": row["review_id"],
                "year": row.get("year") or review.get("year"),
                "period": review.get("period"),
                "trip_type": review.get("trip_type"),
                "rating": review.get("rating"),
                "source_node_raw": row.get("source_node") or "",
                "target_node_raw": row.get("target_node") or "",
                "relation_type_raw": row.get("relation") or "unknown",
                "description": row.get("description"),
                "updated_at": utc_now(),
            },
            "raw_relation_id",
        )

    def process_sentiment(
        self,
        row: Dict[str, Any],
        reviews_by_id: Dict[str, Dict[str, Any]],
    ) -> None:
        resolved = normalize_aspect(row.get("aspect"))
        sentiment_id = self.ensure_sentiment(resolved.aspect, resolved.display_aspect)
        review = reviews_by_id.get(row["review_id"], {})

        self.upsert(
            "sentiment_mentions",
            {
                "raw_sentiment_id": row["id"],
                "sentiment_id": sentiment_id,
                "review_id": row["review_id"],
                "year": row.get("year") or review.get("year"),
                "period": review.get("period"),
                "trip_type": row.get("trip_type") or review.get("trip_type"),
                "rating": row.get("rating") or review.get("rating"),
                "aspect_raw": row.get("aspect") or "",
                "sentiment_label": normalize_sentiment_label(row.get("sentiment")),
                "sentiment_score": row.get("score") if row.get("score") is not None else 0.5,
                "evidence": row.get("evidence"),
                "updated_at": utc_now(),
            },
            "raw_sentiment_id",
        )

    def ensure_entity(
        self,
        raw_name: Any,
        entity_type: Any,
        raw_entity_id: Optional[int] = None,
        review_id: Optional[str] = None,
    ) -> int:
        resolved = self.resolver.resolve(raw_name, entity_type)
        cache_key = (resolved.canonical_name, resolved.entity_type)
        if cache_key in self.entity_id_cache:
            entity_id = self.entity_id_cache[cache_key]
            self.persist_alias(entity_id, raw_name, resolved, raw_entity_id)
            if resolved.is_candidate:
                self.persist_alias_candidate(resolved, raw_name, raw_entity_id, review_id)
            return entity_id

        self.upsert(
            "entities",
            {
                "canonical_name": resolved.canonical_name,
                "display_name": resolved.display_name,
                "entity_type": resolved.entity_type,
                "updated_at": utc_now(),
            },
            "canonical_name,entity_type",
        )
        entity = self.select_one(
            "entities",
            "id,canonical_name,display_name,entity_type",
            {
                "canonical_name": resolved.canonical_name,
                "entity_type": resolved.entity_type,
            },
        )
        self.resolver.add_existing(
            entity["canonical_name"],
            entity["display_name"],
            entity["entity_type"],
            entity["id"],
        )
        self.entity_id_cache[cache_key] = entity["id"]
        self.entities_by_id[entity["id"]] = entity
        self.persist_alias(entity["id"], raw_name, resolved, raw_entity_id)
        if resolved.is_candidate:
            self.persist_alias_candidate(resolved, raw_name, raw_entity_id, review_id)
        return entity["id"]

    def persist_alias(
        self,
        entity_id: int,
        raw_name: Any,
        resolved,
        raw_entity_id: Optional[int] = None,
    ) -> None:
        if resolved.matched_by == "learned_alias":
            return

        normalized_alias = resolved.raw_normalized_alias
        if not normalized_alias:
            return

        source = {
            "learned_alias": "exact",
            "exact": "exact",
            "fuzzy": "fuzzy_auto",
            "token_subset": "token_subset_auto",
            "new": "exact",
            "empty": "exact",
            "fuzzy_candidate": "exact",
            "token_subset_candidate": "exact",
        }.get(resolved.matched_by, "auto")

        self.upsert(
            "entity_aliases",
            {
                "entity_id": entity_id,
                "normalized_alias": normalized_alias,
                "display_alias": str(raw_name or "").strip() or resolved.display_name,
                "entity_type": resolved.entity_type,
                "source": source,
                "confidence": resolved.confidence,
                "scope_type": "global",
                "scope_id": "global",
                "first_seen_raw_id": raw_entity_id,
                "last_seen_raw_id": raw_entity_id,
                "updated_at": utc_now(),
            },
            "normalized_alias,entity_type,scope_type,scope_id",
        )
        self.resolver.add_alias(
            normalized_alias,
            resolved.canonical_name,
            resolved.display_name,
            resolved.entity_type,
            entity_id,
            resolved.confidence,
        )

    def persist_alias_candidate(
        self,
        resolved,
        raw_name: Any,
        raw_entity_id: Optional[int],
        review_id: Optional[str],
    ) -> None:
        if not resolved.suggested_canonical_name:
            return

        suggested_key = (resolved.suggested_canonical_name, resolved.entity_type)
        suggested_entity_id = self.entity_id_cache.get(suggested_key)
        if not suggested_entity_id:
            return

        self.upsert(
            "entity_alias_candidates",
            {
                "normalized_alias": resolved.raw_normalized_alias,
                "display_alias": str(raw_name or "").strip() or resolved.display_name,
                "suggested_entity_id": suggested_entity_id,
                "entity_type": resolved.entity_type,
                "confidence": resolved.confidence,
                "match_method": resolved.matched_by,
                "status": "pending",
                "raw_entity_id": raw_entity_id,
                "review_id": review_id,
                "scope_type": "global",
                "scope_id": "global",
                "updated_at": utc_now(),
            },
            "normalized_alias,entity_type,suggested_entity_id,scope_type,scope_id",
        )

    def ensure_relation(self, source_entity_id: int, target_entity_id: int, relation_type: Any) -> int:
        normalized_type = str(relation_type or "unknown").strip().lower() or "unknown"
        cache_key = (source_entity_id, target_entity_id, normalized_type)
        if cache_key in self.relation_id_cache:
            return self.relation_id_cache[cache_key]

        self.upsert(
            "relations",
            {
                "source_entity_id": source_entity_id,
                "target_entity_id": target_entity_id,
                "relation_type": normalized_type,
                "updated_at": utc_now(),
            },
            "source_entity_id,target_entity_id,relation_type",
        )
        relation = self.select_one(
            "relations",
            "id",
            {
                "source_entity_id": source_entity_id,
                "target_entity_id": target_entity_id,
                "relation_type": normalized_type,
            },
        )
        self.relation_id_cache[cache_key] = relation["id"]
        return relation["id"]

    def ensure_sentiment(self, aspect: str, display_aspect: str) -> int:
        if aspect in self.sentiment_id_cache:
            return self.sentiment_id_cache[aspect]

        self.upsert(
            "sentiments",
            {
                "aspect": aspect,
                "display_aspect": display_aspect,
                "updated_at": utc_now(),
            },
            "aspect",
        )
        sentiment = self.select_one("sentiments", "id", {"aspect": aspect})
        self.sentiment_id_cache[aspect] = sentiment["id"]
        return sentiment["id"]

    def upsert(self, table: str, record: Dict[str, Any], on_conflict: str) -> None:
        self.supabase.table(table).upsert(record, on_conflict=on_conflict).execute()

    def select_one(self, table: str, select: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        query = self.supabase.table(table).select(select)
        for column, value in filters.items():
            query = query.eq(column, value)
        response = query.limit(1).execute()
        if not response.data:
            raise LookupError(f"{table} row not found for filters={filters}")
        return response.data[0]

    def start_run(self) -> int:
        response = (
            self.supabase.table("normalization_runs")
            .insert({"status": "running"})
            .execute()
        )
        run_id = response.data[0]["id"]
        log_event("normalization_started", {"run_id": run_id})
        return run_id

    def finish_run(
        self,
        run_id: int,
        status: str,
        counts: Dict[str, int],
        error_message: Optional[str] = None,
    ) -> None:
        self.supabase.table("normalization_runs").update(
            {
                "status": status,
                "finished_at": utc_now(),
                "entities_processed": counts["entities"],
                "relations_processed": counts["relations"],
                "sentiments_processed": counts["sentiments"],
                "error_message": error_message,
                "updated_at": utc_now(),
            }
        ).eq("id", run_id).execute()

    def mark_checkpoint(
        self,
        raw_table: str,
        raw_id: int,
        run_id: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        self.upsert(
            "normalization_checkpoints",
            {
                "raw_table": raw_table,
                "raw_id": raw_id,
                "run_id": run_id,
                "status": status,
                "error_message": error_message[:500] if error_message else None,
                "updated_at": utc_now(),
            },
            "raw_table,raw_id",
        )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, details: Optional[Dict[str, Any]] = None, level: str = "INFO") -> None:
    print(json.dumps({"event": event, "level": level, **(details or {})}), file=sys.stderr)
