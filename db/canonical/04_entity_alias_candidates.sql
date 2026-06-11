-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: entity_alias_candidates
-- ═══════════════════════════════════════════════════════════════════
-- Ambiguous alias suggestions that should be reviewed before promotion
-- to entity_aliases.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS entity_alias_candidates (
    id                    BIGSERIAL PRIMARY KEY,
    normalized_alias      TEXT NOT NULL,
    display_alias         TEXT NOT NULL,
    suggested_entity_id   BIGINT NOT NULL REFERENCES entities(id),
    entity_type           TEXT NOT NULL,
    confidence            NUMERIC NOT NULL,
    match_method          TEXT NOT NULL,
    status                TEXT NOT NULL DEFAULT 'pending',
    raw_entity_id         BIGINT,
    review_id             TEXT,
    scope_type            TEXT NOT NULL DEFAULT 'global',
    scope_id              TEXT NOT NULL DEFAULT 'global',
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (normalized_alias, entity_type, suggested_entity_id, scope_type, scope_id)
);

COMMENT ON TABLE entity_alias_candidates IS 'Review queue for uncertain entity alias mappings.';
COMMENT ON COLUMN entity_alias_candidates.status IS 'pending | approved | rejected';
COMMENT ON COLUMN entity_alias_candidates.match_method IS 'fuzzy_candidate | embedding_candidate | other';
