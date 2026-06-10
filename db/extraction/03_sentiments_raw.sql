-- ═══════════════════════════════════════════════════════════════════
-- EXTRACTION TABLE: sentiments_raw
-- ═══════════════════════════════════════════════════════════════════
-- Raw extracted aspect-level sentiments from LLM processing (Job 2)
-- Source: llm-extract/transformer.py → transform_extraction()
-- Aspects: service, facility, environment, ritual_experience,
--          spiritual_authenticity, access_fairness, sacred_atmosphere,
--          crowd_management, cultural_sensitivity
-- Sentiment values: positive | neutral | negative
-- Score range: 0.0 - 1.0
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS sentiments_raw CASCADE;

CREATE TABLE sentiments_raw (
    id              BIGSERIAL PRIMARY KEY,
    review_id       TEXT NOT NULL,
    year            INTEGER,
    trip_type       TEXT,
    aspect          TEXT NOT NULL,
    sentiment       TEXT NOT NULL,
    score           NUMERIC NOT NULL,
    evidence        TEXT,
    rating          NUMERIC,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table comment
COMMENT ON TABLE sentiments_raw IS 'Raw aspect-level sentiments extracted by LLM from reviews. One row per aspect per review.';

-- Column comments
COMMENT ON COLUMN sentiments_raw.aspect IS 'One of 9 aspects: service, facility, environment, ritual_experience, spiritual_authenticity, access_fairness, sacred_atmosphere, crowd_management, cultural_sensitivity';
COMMENT ON COLUMN sentiments_raw.sentiment IS 'One of: positive, neutral, negative';
COMMENT ON COLUMN sentiments_raw.score IS 'Sentiment score 0.0-1.0 (0.0-0.2=strongly negative, 0.3-0.4=mildly negative, 0.6-0.7=mildly positive, 0.8-0.9=strongly positive, 1.0=superlative)';
COMMENT ON COLUMN sentiments_raw.evidence IS 'Direct quote from review supporting the sentiment';