-- ═══════════════════════════════════════════════════════════════════
-- CORE TABLE: scrape_runs
-- ═══════════════════════════════════════════════════════════════════
-- Scrape run tracking table populated by Job 1 (Scraper)
-- Source: scraper/clean_and_upload.py → process_and_upload()
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS scrape_runs CASCADE;

CREATE TABLE scrape_runs (
    -- Primary identifier
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT UNIQUE NOT NULL,

    -- Run metadata
    run_date        TEXT,          -- Format: YYYYMMDD_HHMMSS
    scraped_at      TIMESTAMP,

    -- Volume metrics
    total_reviews   INTEGER DEFAULT 0,
    new_reviews     INTEGER DEFAULT 0,
    total_pages     INTEGER DEFAULT 0,

    -- Storage reference
    storage_path    TEXT,          -- e.g., 'supabase_postgresql_table'

    -- Timestamps
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by run_date
CREATE INDEX idx_scrape_runs_run_date ON scrape_runs(run_date DESC);
CREATE INDEX idx_scrape_runs_created_at ON scrape_runs(created_at DESC);

-- Table comment
COMMENT ON TABLE scrape_runs IS 'Tracks each scrape run from Job 1. One row per scrape execution.';

-- Column comments
COMMENT ON COLUMN scrape_runs.run_id IS 'Unique run identifier (format: YYYYMMDD_HHMMSS)';
COMMENT ON COLUMN scrape_runs.total_reviews IS 'Total reviews processed in this run (including duplicates)';
COMMENT ON COLUMN scrape_runs.new_reviews IS 'Number of new reviews actually inserted into cleaned_reviews';
COMMENT ON COLUMN scrape_runs.storage_path IS 'Indicates where data is stored (always supabase_postgresql_table)';