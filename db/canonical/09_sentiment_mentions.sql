-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: sentiment_mentions
-- ═══════════════════════════════════════════════════════════════════
-- Mention-level provenance for canonical aspect sentiments.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sentiment_mentions (
    id                BIGSERIAL PRIMARY KEY,
    raw_sentiment_id  BIGINT UNIQUE NOT NULL,
    sentiment_id      BIGINT NOT NULL REFERENCES sentiments(id),
    review_id         TEXT NOT NULL,
    year              INTEGER,
    period            TEXT,
    trip_type         TEXT,
    rating            NUMERIC,
    aspect_raw        TEXT NOT NULL,
    sentiment_label   TEXT NOT NULL,
    sentiment_score   NUMERIC NOT NULL,
    evidence          TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sentiment_mentions IS 'One row per raw aspect sentiment after aspect normalization. Preserves review-level evidence.';
COMMENT ON COLUMN sentiment_mentions.raw_sentiment_id IS 'sentiments_raw.id; unique to keep normalization rerunnable without duplicates';
