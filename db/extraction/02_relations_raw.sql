-- ═══════════════════════════════════════════════════════════════════
-- EXTRACTION TABLE: relations_raw
-- ═══════════════════════════════════════════════════════════════════
-- Raw extracted relations between entities from LLM processing (Job 2)
-- Source: llm-extract/transformer.py → transform_extraction()
-- Relation types: co_occurrence | causal | description | contrast
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS relations_raw CASCADE;

CREATE TABLE relations_raw (
    id              BIGSERIAL PRIMARY KEY,
    review_id       TEXT NOT NULL,
    year            INTEGER,
    source_node     TEXT NOT NULL,
    target_node     TEXT NOT NULL,
    relation        TEXT NOT NULL,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table comment
COMMENT ON TABLE relations_raw IS 'Raw relations between entities extracted by LLM from reviews. One row per relation per review.';

-- Column comments
COMMENT ON COLUMN relations_raw.source_node IS 'Source entity name (matches entities_raw.entity_name)';
COMMENT ON COLUMN relations_raw.target_node IS 'Target entity name (matches entities_raw.entity_name)';
COMMENT ON COLUMN relations_raw.relation IS 'One of 4 types: co_occurrence, causal, description, contrast';
COMMENT ON COLUMN relations_raw.description IS 'Brief reason for the relation';