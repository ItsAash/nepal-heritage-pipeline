-- ═══════════════════════════════════════════════════════════════════
-- CORE TABLE INDEXES
-- ═══════════════════════════════════════════════════════════════════
-- Indexes for cleaned_reviews and scrape_runs tables
-- ═══════════════════════════════════════════════════════════════════

-- cleaned_reviews indexes
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_review_id ON cleaned_reviews(review_id);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_year ON cleaned_reviews(year);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_period ON cleaned_reviews(period);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_trip_type ON cleaned_reviews(trip_type);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_sentiment ON cleaned_reviews(sentiment_class);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_run_id ON cleaned_reviews(run_id);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_ingested_at ON cleaned_reviews(ingested_at);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_has_sacred ON cleaned_reviews(has_sacred_content);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_rating ON cleaned_reviews(rating);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_year_period ON cleaned_reviews(year, period);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_trip_sentiment ON cleaned_reviews(trip_type, sentiment_class);
CREATE INDEX IF NOT EXISTS idx_cleaned_reviews_sacred_year ON cleaned_reviews(has_sacred_content, year);

-- scrape_runs indexes
CREATE INDEX IF NOT EXISTS idx_scrape_runs_run_id ON scrape_runs(run_id);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_run_date ON scrape_runs(run_date DESC);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_created_at ON scrape_runs(created_at DESC);

-- Index comments
COMMENT ON INDEX idx_cleaned_reviews_year IS 'Filters reviews by year for temporal analysis';
COMMENT ON INDEX idx_cleaned_reviews_period IS 'Filters by COVID-era period classification';
COMMENT ON INDEX idx_cleaned_reviews_trip_type IS 'Filters by trip type (solo, family, couple, etc.)';
COMMENT ON INDEX idx_cleaned_reviews_has_sacred IS 'Filters reviews with sacred content for heritage analysis';
COMMENT ON INDEX idx_cleaned_reviews_sacred_year IS 'Composite for sacred content analysis by year';