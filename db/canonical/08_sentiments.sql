-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: sentiments
-- ═══════════════════════════════════════════════════════════════════
-- Canonical aspect-level sentiment aggregates.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sentiments (
    id                   BIGSERIAL PRIMARY KEY,
    aspect               TEXT UNIQUE NOT NULL,
    display_aspect       TEXT NOT NULL,
    positive_count       INTEGER DEFAULT 0,
    neutral_count        INTEGER DEFAULT 0,
    negative_count       INTEGER DEFAULT 0,
    mention_count        INTEGER DEFAULT 0,
    avg_sentiment_score  NUMERIC,
    first_seen_year      INTEGER,
    last_seen_year       INTEGER,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sentiments IS 'Canonical aspect-level sentiment aggregates derived from sentiments_raw.';
COMMENT ON COLUMN sentiments.aspect IS 'Stable normalized aspect key, e.g. ritual_experience';
