-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: entity_mentions
-- ═══════════════════════════════════════════════════════════════════
-- Provenance for entities: links raw record to canonical entity.
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS entity_mentions CASCADE;

CREATE TABLE entity_mentions (
    id                  BIGSERIAL PRIMARY KEY,
    entity_id           BIGINT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    review_id           TEXT NOT NULL,
    raw_entity_id       BIGINT NOT NULL,
    entity_name_raw     TEXT,
    normalized_alias    TEXT,
    entity_type_raw     TEXT,
    quote               TEXT,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_entity_id)
);

-- Index for join performance
CREATE INDEX idx_entity_mentions_review_id ON entity_mentions(review_id);
CREATE INDEX idx_entity_mentions_entity_id ON entity_mentions(entity_id);

-- Table comment
COMMENT ON TABLE entity_mentions IS 'Provenance for entities. Links raw LLM extraction to canonical entity nodes.';
