-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: entities
-- ═══════════════════════════════════════════════════════════════════
-- Deduplicated entity nodes derived from entities_raw.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS entities (
    id               BIGSERIAL PRIMARY KEY,
    canonical_name   TEXT NOT NULL,
    display_name     TEXT NOT NULL,
    entity_type      TEXT NOT NULL,
    mention_count    INTEGER DEFAULT 0,
    first_seen_year  INTEGER,
    last_seen_year   INTEGER,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (canonical_name, entity_type)
);

COMMENT ON TABLE entities IS 'Canonical entity nodes for network and heritage knowledge graph analysis.';
COMMENT ON COLUMN entities.canonical_name IS 'Stable normalized key, e.g. bagmati_river';
COMMENT ON COLUMN entities.display_name IS 'Human-readable canonical label, e.g. Bagmati River';
COMMENT ON COLUMN entities.entity_type IS 'Canonical entity type inherited from entities_raw.entity_type';
