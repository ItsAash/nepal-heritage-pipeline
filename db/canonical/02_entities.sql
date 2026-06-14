-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: entities
-- ═══════════════════════════════════════════════════════════════════
-- Deduplicated entity nodes derived from entities_raw.
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS entities CASCADE;

CREATE TABLE entities (
    id               BIGSERIAL PRIMARY KEY,
    canonical_name   TEXT NOT NULL,
    display_name     TEXT NOT NULL,
    entity_type      TEXT NOT NULL,
    
    -- Aggregated metrics (updated by refresh_canonical_aggregates)
    mention_count    INTEGER DEFAULT 0,
    first_seen_year  INTEGER,
    last_seen_year   INTEGER,
    
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (canonical_name, entity_type)
);

-- Table comment
COMMENT ON TABLE entities IS 'Canonical entity nodes for network and heritage knowledge graph analysis.';
COMMENT ON COLUMN entities.canonical_name IS 'Stable normalized key, e.g. bagmati_river';
COMMENT ON COLUMN entities.display_name IS 'Human-readable canonical label, e.g. Bagmati River';
