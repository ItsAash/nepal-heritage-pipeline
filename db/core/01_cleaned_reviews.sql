-- ═══════════════════════════════════════════════════════════════════
-- CORE TABLE: cleaned_reviews
-- ═══════════════════════════════════════════════════════════════════
-- Main review storage table populated by Job 1 (Scraper)
-- Source: scraper/clean_and_upload.py → process_and_upload()
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS cleaned_reviews CASCADE;

CREATE TABLE cleaned_reviews (
    -- Primary identifier
    review_id         TEXT PRIMARY KEY,

    -- Cleaned review content
    title_clean       TEXT,
    text_clean        TEXT NOT NULL,

    -- Rating & sentiment
    rating            NUMERIC,
    sentiment_class   TEXT,          -- 'positive' | 'neutral' | 'negative' | 'unknown'

    -- Date fields
    date              TEXT,          -- Original published date string (YYYY-MM-DD)
    year              INTEGER,
    month             INTEGER,
    quarter           INTEGER,

    -- Period classification (COVID-era)
    period            TEXT,          -- 'pre_covid_peak' | 'covid_onset' | 'covid_deep' | 'recovery_early' | 'recovery_late' | 'post_recovery' | 'early_period' | 'growth_period' | 'unknown'

    -- Trip metadata
    trip_type         TEXT,          -- 'solo' | 'family' | 'couple' | 'friends' | 'business' | 'unknown'
    reviewer_type     TEXT,          -- 'likely_pilgrim' | 'mixed' | 'likely_tourist'
    reviewer_name     TEXT,

    -- Text metrics
    word_count        INTEGER DEFAULT 0,
    like_count        INTEGER DEFAULT 0,

    -- Image metadata
    has_images        BOOLEAN DEFAULT FALSE,
    image_count       INTEGER DEFAULT 0,
    image_urls        TEXT,          -- Pipe-separated URLs

    -- Sacred content flags (from keyword detection)
    has_sacred_content BOOLEAN DEFAULT FALSE,
    has_ritual         BOOLEAN DEFAULT FALSE,
    has_actor          BOOLEAN DEFAULT FALSE,
    has_space          BOOLEAN DEFAULT FALSE,
    has_spiritual      BOOLEAN DEFAULT FALSE,
    has_festival       BOOLEAN DEFAULT FALSE,
    has_rule           BOOLEAN DEFAULT FALSE,

    -- Language metadata
    language          TEXT DEFAULT 'en',
    is_translated     BOOLEAN DEFAULT FALSE,
    original_language TEXT DEFAULT 'en',

    -- Source link
    review_link       TEXT,

    -- Run tracking
    run_id            TEXT NOT NULL,
    ingested_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table comment
COMMENT ON TABLE cleaned_reviews IS 'Main review storage from Job 1 scraper. One row per unique review_id.';

-- Column comments
COMMENT ON COLUMN cleaned_reviews.review_id IS 'Unique TripAdvisor review identifier (primary key)';
COMMENT ON COLUMN cleaned_reviews.text_clean IS 'Cleaned review text (NFC normalized, URLs/entities removed)';
COMMENT ON COLUMN cleaned_reviews.period IS 'COVID-era classification based on review year';
COMMENT ON COLUMN cleaned_reviews.reviewer_type IS 'Proxy for pilgrim vs tourist based on trip_type';
COMMENT ON COLUMN cleaned_reviews.has_sacred_content IS 'True if any sacred keyword category matched';
COMMENT ON COLUMN cleaned_reviews.run_id IS 'Scrape run identifier linking to scrape_runs table';