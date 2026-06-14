-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: relation_mentions
-- ═══════════════════════════════════════════════════════════════════
-- Provenance for relations: links raw record to canonical relation.
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS relation_mentions CASCADE;

CREATE TABLE relation_mentions (
    id                  BIGSERIAL PRIMARY KEY,
    relation_id         BIGINT NOT NULL REFERENCES relations(id) ON DELETE CASCADE,
    review_id           TEXT NOT NULL,
    raw_relation_id     BIGINT NOT NULL,
    source_node_raw     TEXT,
    target_node_raw     TEXT,
    relation_type_raw   TEXT,
    description         TEXT,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_relation_id)
);

-- Index for join performance
CREATE INDEX idx_relation_mentions_review_id ON relation_mentions(review_id);
CREATE INDEX idx_relation_mentions_relation_id ON relation_mentions(relation_id);

-- Table comment
COMMENT ON TABLE relation_mentions IS 'Provenance for relations. Links raw LLM extraction to canonical relation edges.';
