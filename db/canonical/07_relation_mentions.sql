-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: relation_mentions
-- ═══════════════════════════════════════════════════════════════════
-- Mention-level provenance for canonical relations.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS relation_mentions (
    id                 BIGSERIAL PRIMARY KEY,
    raw_relation_id    BIGINT UNIQUE NOT NULL,
    relation_id        BIGINT NOT NULL REFERENCES relations(id),
    review_id          TEXT NOT NULL,
    year               INTEGER,
    period             TEXT,
    trip_type          TEXT,
    rating             NUMERIC,
    source_node_raw    TEXT NOT NULL,
    target_node_raw    TEXT NOT NULL,
    relation_type_raw  TEXT NOT NULL,
    description        TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE relation_mentions IS 'One row per raw relation mention after canonical source/target resolution.';
COMMENT ON COLUMN relation_mentions.raw_relation_id IS 'relations_raw.id; unique to keep normalization rerunnable without duplicates';
