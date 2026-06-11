-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: relations
-- ═══════════════════════════════════════════════════════════════════
-- Deduplicated weighted graph edges between canonical entities.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS relations (
    id                BIGSERIAL PRIMARY KEY,
    source_entity_id  BIGINT NOT NULL REFERENCES entities(id),
    target_entity_id  BIGINT NOT NULL REFERENCES entities(id),
    relation_type     TEXT NOT NULL,
    weight            INTEGER DEFAULT 0,
    first_seen_year   INTEGER,
    last_seen_year    INTEGER,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_entity_id, target_entity_id, relation_type)
);

COMMENT ON TABLE relations IS 'Canonical weighted relation edges for knowledge graph construction.';
COMMENT ON COLUMN relations.weight IS 'Number of relation_mentions supporting this canonical edge';
