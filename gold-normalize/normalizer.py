"""
Pure normalization helpers for the standalone Gold Canonical workflow.
"""

import re
import string
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, Optional

from aliases import ALIAS_EXTRA_TOKENS, TOKEN_EQUIVALENTS

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - exercised only without optional dependency
    fuzz = None


PUNCT_TRANSLATION = str.maketrans({char: " " for char in string.punctuation})


@dataclass(frozen=True)
class ResolvedEntity:
    canonical_name: str
    display_name: str
    entity_type: str
    matched_by: str
    confidence: float
    raw_normalized_alias: str
    is_candidate: bool = False
    suggested_canonical_name: Optional[str] = None
    suggested_display_name: Optional[str] = None


@dataclass(frozen=True)
class ResolvedAspect:
    aspect: str
    display_aspect: str


def normalize_label(value: Any) -> str:
    """Normalize text for dictionary lookup and fuzzy matching."""
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = text.strip().lower()
    text = text.replace("&", " and ")
    text = text.translate(PUNCT_TRANSLATION)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def slugify(value: Any) -> str:
    normalized = normalize_label(value)
    return normalized.replace(" ", "_")


def display_from_key(canonical_name: str) -> str:
    return canonical_name.replace("_", " ").title()


def similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if fuzz is not None:
        return float(fuzz.token_sort_ratio(left, right))
    return SequenceMatcher(None, left, right).ratio() * 100


def equivalent_token(token: str) -> str:
    return TOKEN_EQUIVALENTS.get(token, token)


def equivalent_label(value: str) -> str:
    return " ".join(equivalent_token(token) for token in normalize_label(value).split())


def token_set(value: str) -> set[str]:
    return set(equivalent_label(value).split())


def automatic_alias_score(raw_label: str, candidate_label: str) -> tuple[float, str]:
    """
    Score whether two labels should be aliases without any named dictionary.

    The token-subset rule handles scalable cases like:
    - Bagmati -> Bagmati River
    - Evening Aarti -> Aarti
    - Cremation Ceremony -> Cremation
    while still penalizing unrelated extra content.
    """
    raw = normalize_label(raw_label)
    candidate = normalize_label(candidate_label)
    if not raw or not candidate:
        return 0.0, "empty"
    if raw == candidate:
        return 100.0, "exact"

    equivalent_raw = equivalent_label(raw)
    equivalent_candidate = equivalent_label(candidate)
    if equivalent_raw == equivalent_candidate:
        return 98.0, "token_equivalent"

    fuzzy_score = max(
        similarity(raw, candidate),
        similarity(equivalent_raw, equivalent_candidate),
    )
    raw_tokens = token_set(raw)
    candidate_tokens = token_set(candidate)

    if raw_tokens and candidate_tokens:
        smaller = raw_tokens if len(raw_tokens) <= len(candidate_tokens) else candidate_tokens
        larger = candidate_tokens if smaller is raw_tokens else raw_tokens
        extra = larger - smaller
        overlap_ratio = len(raw_tokens & candidate_tokens) / max(len(raw_tokens | candidate_tokens), 1)

        equivalent_extra = {equivalent_token(token) for token in extra}
        if smaller.issubset(larger) and equivalent_extra.issubset(ALIAS_EXTRA_TOKENS):
            subset_score = 96.0 if overlap_ratio >= 0.5 else 88.0
            return max(fuzzy_score, subset_score), "token_subset"

    return fuzzy_score, "fuzzy"


@dataclass(frozen=True)
class AliasMatch:
    entity_id: int
    canonical_name: str
    display_name: str
    entity_type: str
    confidence: float


class EntityResolver:
    """Resolve raw entity names to stable canonical entity keys."""

    def __init__(self, auto_threshold: int = 95, candidate_threshold: int = 75):
        self.auto_threshold = auto_threshold
        self.candidate_threshold = candidate_threshold
        self._existing_by_type: Dict[str, Dict[str, str]] = {}
        self._entity_ids_by_key: Dict[tuple[str, str], int] = {}
        self._aliases_by_type: Dict[str, Dict[str, AliasMatch]] = {}

    def add_existing(self, canonical_name: str, display_name: str, entity_type: str, entity_id: int | None = None) -> None:
        entity_type = entity_type or "unknown"
        self._existing_by_type.setdefault(entity_type, {})[canonical_name] = display_name
        if entity_id is not None:
            self._entity_ids_by_key[(canonical_name, entity_type)] = entity_id

    def extend_existing(self, entities: Iterable[Dict[str, Any]]) -> None:
        for entity in entities:
            self.add_existing(
                entity["canonical_name"],
                entity["display_name"],
                entity.get("entity_type") or "unknown",
                entity.get("id"),
            )

    def add_alias(
        self,
        normalized_alias: str,
        canonical_name: str,
        display_name: str,
        entity_type: str,
        entity_id: int,
        confidence: float = 1.0,
    ) -> None:
        entity_type = entity_type or "unknown"
        alias = normalize_label(normalized_alias)
        self._aliases_by_type.setdefault(entity_type, {})[alias] = AliasMatch(
            entity_id=entity_id,
            canonical_name=canonical_name,
            display_name=display_name,
            entity_type=entity_type,
            confidence=confidence,
        )

    def extend_aliases(self, aliases: Iterable[Dict[str, Any]]) -> None:
        for alias in aliases:
            entity = alias.get("entities") or {}
            canonical_name = entity.get("canonical_name")
            display_name = entity.get("display_name")
            if not canonical_name or not display_name:
                continue
            self.add_alias(
                alias["normalized_alias"],
                canonical_name,
                display_name,
                alias.get("entity_type") or entity.get("entity_type") or "unknown",
                alias["entity_id"],
                float(alias.get("confidence") or 1.0),
            )

    def resolve(self, raw_name: Any, entity_type: Any) -> ResolvedEntity:
        normalized = normalize_label(raw_name)
        resolved_type = str(entity_type or "unknown").strip().lower() or "unknown"

        if not normalized:
            return ResolvedEntity(
                canonical_name="unknown",
                display_name="Unknown",
                entity_type=resolved_type,
                matched_by="empty",
                confidence=1.0,
                raw_normalized_alias=normalized,
            )

        approved_alias = self._aliases_by_type.get(resolved_type, {}).get(normalized)
        if approved_alias:
            return ResolvedEntity(
                canonical_name=approved_alias.canonical_name,
                display_name=approved_alias.display_name,
                entity_type=resolved_type,
                matched_by="learned_alias",
                confidence=approved_alias.confidence,
                raw_normalized_alias=normalized,
            )

        existing = self._existing_by_type.get(resolved_type, {})
        best_key: Optional[str] = None
        best_method = "fuzzy"
        best_score = 0.0
        for canonical_name, display_name in existing.items():
            score, method = automatic_alias_score(normalized, display_name)
            if score > best_score:
                best_score = score
                best_key = canonical_name
                best_method = method

        if best_key and best_score >= self.auto_threshold:
            return ResolvedEntity(
                canonical_name=best_key,
                display_name=existing[best_key],
                entity_type=resolved_type,
                matched_by=best_method,
                confidence=best_score / 100,
                raw_normalized_alias=normalized,
            )

        if best_key and best_score >= self.candidate_threshold:
            canonical_name = slugify(normalized)
            return ResolvedEntity(
                canonical_name=canonical_name,
                display_name=display_from_key(canonical_name),
                entity_type=resolved_type,
                matched_by=f"{best_method}_candidate",
                confidence=best_score / 100,
                raw_normalized_alias=normalized,
                is_candidate=True,
                suggested_canonical_name=best_key,
                suggested_display_name=existing[best_key],
            )

        canonical_name = slugify(normalized)
        return ResolvedEntity(
            canonical_name=canonical_name,
            display_name=display_from_key(canonical_name),
            entity_type=resolved_type,
            matched_by="new",
            confidence=1.0,
            raw_normalized_alias=normalized,
        )


def normalize_aspect(raw_aspect: Any) -> ResolvedAspect:
    normalized = normalize_label(raw_aspect)
    aspect = slugify(normalized)
    return ResolvedAspect(aspect=aspect, display_aspect=aspect.replace("_", " ").title())


def normalize_sentiment_label(raw_label: Any) -> str:
    label = normalize_label(raw_label)
    if label in {"positive", "neutral", "negative"}:
        return label
    if label in {"pos", "good", "favorable"}:
        return "positive"
    if label in {"neg", "bad", "unfavorable"}:
        return "negative"
    return "neutral"


def relation_endpoint_from_review_entities(
    raw_node: Any,
    review_entities: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Resolve relation endpoints stored as either entity names or old numeric LLM IDs.

    Historical rows may contain "1" and "2" because the extraction prompt used
    numeric entity IDs. We map those back to entity insertion order per review.
    """
    entities = sorted(list(review_entities), key=lambda row: row.get("id") or 0)
    raw_text = str(raw_node or "").strip()

    if raw_text.isdigit():
        index = int(raw_text) - 1
        if 0 <= index < len(entities):
            return entities[index]

    normalized = normalize_label(raw_text)
    for entity in entities:
        if normalize_label(entity.get("entity_name")) == normalized:
            return entity

    return {
        "entity_name": raw_text,
        "entity_type": "unknown",
    }
