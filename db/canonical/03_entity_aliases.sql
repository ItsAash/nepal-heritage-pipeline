-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: entity_aliases
-- ═══════════════════════════════════════════════════════════════════
-- Approved alias mappings from noisy raw entity labels to canonical entities.
-- This table is the learned replacement for a static in-code alias dictionary.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS entity_aliases (
    id                   BIGSERIAL PRIMARY KEY,
    entity_id            BIGINT NOT NULL REFERENCES entities(id),
    normalized_alias     TEXT NOT NULL,
    display_alias        TEXT NOT NULL,
    entity_type          TEXT NOT NULL,
    source               TEXT NOT NULL DEFAULT 'auto',
    confidence           NUMERIC NOT NULL DEFAULT 1.0,
    scope_type           TEXT NOT NULL DEFAULT 'global',
    scope_id             TEXT NOT NULL DEFAULT 'global',
    first_seen_raw_id    BIGINT,
    last_seen_raw_id     BIGINT,
    mention_count        INTEGER DEFAULT 0,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (normalized_alias, entity_type, scope_type, scope_id)
);

COMMENT ON TABLE entity_aliases IS 'Approved learned aliases mapping normalized raw entity labels to canonical entities.';
COMMENT ON COLUMN entity_aliases.source IS 'exact | fuzzy_auto | token_subset_auto | manual';
COMMENT ON COLUMN entity_aliases.scope_type IS 'global | country | destination | attraction | industry; global until multi-site metadata exists';
COMMENT ON COLUMN entity_aliases.scope_id IS 'Optional scope identifier for future multi-site or cross-industry expansion';
COMMENT ON COLUMN entity_aliases.confidence IS 'Alias confidence from 0.0 to 1.0';
