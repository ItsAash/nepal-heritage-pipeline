-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: relations
-- ═══════════════════════════════════════════════════════════════════
-- Deduplicated relations between canonical entities.
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS relations CASCADE;

CREATE TABLE relations (
    id                  BIGSERIAL PRIMARY KEY,
    source_entity_id    BIGINT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id    BIGINT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type       TEXT NOT NULL,
    
    -- Aggregated metrics
    weight              INTEGER DEFAULT 1,
    first_seen_year     INTEGER,
    last_seen_year      INTEGER,
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_entity_id, target_entity_id, relation_type)
);

-- Table comment
COMMENT ON TABLE relations IS 'Canonical relation edges between entity nodes.';
COMMENT ON COLUMN relations.weight IS 'Number of times this relation appeared across all reviews';
