-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: sentiment_mentions
-- ═══════════════════════════════════════════════════════════════════
-- Provenance for sentiments: links raw record to canonical sentiment.
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS sentiment_mentions CASCADE;

CREATE TABLE sentiment_mentions (
    id                  BIGSERIAL PRIMARY KEY,
    sentiment_id        BIGINT NOT NULL REFERENCES sentiments(id) ON DELETE CASCADE,
    review_id           TEXT NOT NULL,
    raw_sentiment_id    BIGINT NOT NULL,
    aspect_raw          TEXT,
    sentiment_label     TEXT,
    sentiment_score     NUMERIC,
    evidence            TEXT,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_sentiment_id)
);

-- Index for join performance
CREATE INDEX idx_sentiment_mentions_review_id ON sentiment_mentions(review_id);
CREATE INDEX idx_sentiment_mentions_sentiment_id ON sentiment_mentions(sentiment_id);

-- Table comment
COMMENT ON TABLE sentiment_mentions IS 'Provenance for sentiments. Links raw LLM extraction to canonical entity sentiment.';
