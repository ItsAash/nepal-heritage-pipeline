-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: entity_aliases
-- ═══════════════════════════════════════════════════════════════════
-- Maps raw normalized aliases to canonical entities.
-- Merged: entity_aliases + entity_alias_candidates
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS entity_aliases CASCADE;

CREATE TABLE entity_aliases (
    id                  BIGSERIAL PRIMARY KEY,
    entity_id           BIGINT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    normalized_alias    TEXT NOT NULL,
    display_alias       TEXT,
    entity_type         TEXT NOT NULL,
    confidence          NUMERIC DEFAULT 1.0,
    mention_count       INTEGER DEFAULT 0,
    
    -- Status: 'approved' (trusted) | 'pending' (suggested candidate)
    status              TEXT NOT NULL DEFAULT 'approved',
    
    -- Provenance
    source              TEXT, -- 'exact' | 'fuzzy' | 'token_subset' | 'manual'
    match_method        TEXT,
    suggested_merge_entity_id BIGINT REFERENCES entities(id) ON DELETE SET NULL,
    scope_type          TEXT DEFAULT 'global',
    scope_id            TEXT DEFAULT 'global',
    first_seen_raw_id   BIGINT,
    last_seen_raw_id    BIGINT,
    
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (normalized_alias, entity_type, scope_type, scope_id)
);

-- Table comment
COMMENT ON TABLE entity_aliases IS 'Mapping of raw aliases to canonical entities. includes both approved aliases and pending candidates.';

-- Column comments
COMMENT ON COLUMN entity_aliases.status IS 'approved: trusted mapping; pending: suggested candidate for review';
COMMENT ON COLUMN entity_aliases.normalized_alias IS 'Normalized string used for lookup';
COMMENT ON COLUMN entity_aliases.confidence IS 'Matching confidence score (0.0-1.0)';
