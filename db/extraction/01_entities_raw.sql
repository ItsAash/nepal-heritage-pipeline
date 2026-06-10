-- ═══════════════════════════════════════════════════════════════════
-- EXTRACTION TABLE: entities_raw
-- ═══════════════════════════════════════════════════════════════════
-- Raw extracted entities from LLM processing (Job 2)
-- Source: llm-extract/transformer.py → transform_extraction()
-- Entity types: scenic_spot, problem, facility_service, general_sentiment,
--               ritual, religious_actor, sacred_space, spiritual_emotion,
--               festival_event, cultural_rule, sacred_object, dual_valence
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS entities_raw CASCADE;

CREATE TABLE entities_raw (
    id              BIGSERIAL PRIMARY KEY,
    review_id       TEXT NOT NULL,
    year            INTEGER,
    period          TEXT,
    trip_type       TEXT,
    entity_name     TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    quote           TEXT,
    rating          NUMERIC,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table comment
COMMENT ON TABLE entities_raw IS 'Raw entities extracted by LLM from reviews. One row per entity per review.';

-- Column comments
COMMENT ON COLUMN entities_raw.entity_name IS 'Exact phrase from review text (not normalized)';
COMMENT ON COLUMN entities_raw.entity_type IS 'One of 12 types: scenic_spot, problem, facility_service, general_sentiment, ritual, religious_actor, sacred_space, spiritual_emotion, festival_event, cultural_rule, sacred_object, dual_valence';
COMMENT ON COLUMN entities_raw.quote IS '2-6 word supporting quote from review text';