-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: sentiments
-- ═══════════════════════════════════════════════════════════════════
-- Aggregated sentiment profiles per canonical entity.
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS sentiments CASCADE;

CREATE TABLE sentiments (
    id                  BIGSERIAL PRIMARY KEY,
    aspect              TEXT NOT NULL UNIQUE,
    display_aspect      TEXT,
    
    -- Sentiment counts
    positive_count      INTEGER DEFAULT 0,
    neutral_count       INTEGER DEFAULT 0,
    negative_count      INTEGER DEFAULT 0,
    mention_count       INTEGER DEFAULT 0,
    
    -- Aggregate metrics
    avg_sentiment_score NUMERIC DEFAULT 0.5,
    first_seen_year     INTEGER,
    last_seen_year      INTEGER,
    
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table comment
COMMENT ON TABLE sentiments IS 'Aggregated sentiment profiles per canonical aspect.';
COMMENT ON COLUMN sentiments.avg_sentiment_score IS 'Mean sentiment score (0.0-1.0) across all mentions';
