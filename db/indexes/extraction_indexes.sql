-- ═══════════════════════════════════════════════════════════════════
-- EXTRACTION TABLE INDEXES
-- ═══════════════════════════════════════════════════════════════════
-- Indexes for entities_raw, relations_raw, sentiments_raw, extraction_checkpoint
-- ═══════════════════════════════════════════════════════════════════

-- entities_raw indexes
CREATE INDEX IF NOT EXISTS idx_entities_raw_review_id ON entities_raw(review_id);
CREATE INDEX IF NOT EXISTS idx_entities_raw_entity_type ON entities_raw(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_raw_year ON entities_raw(year);
CREATE INDEX IF NOT EXISTS idx_entities_raw_period ON entities_raw(period);
CREATE INDEX IF NOT EXISTS idx_entities_raw_trip_type ON entities_raw(trip_type);
CREATE INDEX IF NOT EXISTS idx_entities_raw_entity_name ON entities_raw(entity_name);

-- Composite indexes for entities
CREATE INDEX IF NOT EXISTS idx_entities_raw_type_year ON entities_raw(entity_type, year);
CREATE INDEX IF NOT EXISTS idx_entities_raw_review_type ON entities_raw(review_id, entity_type);

-- relations_raw indexes
CREATE INDEX IF NOT EXISTS idx_relations_raw_review_id ON relations_raw(review_id);
CREATE INDEX IF NOT EXISTS idx_relations_raw_relation ON relations_raw(relation);
CREATE INDEX IF NOT EXISTS idx_relations_raw_year ON relations_raw(year);
CREATE INDEX IF NOT EXISTS idx_relations_raw_source ON relations_raw(source_node);
CREATE INDEX IF NOT EXISTS idx_relations_raw_target ON relations_raw(target_node);

-- Composite indexes for relations
CREATE INDEX IF NOT EXISTS idx_relations_raw_source_target ON relations_raw(source_node, target_node);
CREATE INDEX IF NOT EXISTS idx_relations_raw_review_relation ON relations_raw(review_id, relation);

-- sentiments_raw indexes
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_review_id ON sentiments_raw(review_id);
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_aspect ON sentiments_raw(aspect);
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_sentiment ON sentiments_raw(sentiment);
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_year ON sentiments_raw(year);
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_trip_type ON sentiments_raw(trip_type);
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_score ON sentiments_raw(score);

-- Composite indexes for sentiments
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_aspect_sentiment ON sentiments_raw(aspect, sentiment);
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_aspect_year ON sentiments_raw(aspect, year);
CREATE INDEX IF NOT EXISTS idx_sentiments_raw_review_aspect ON sentiments_raw(review_id, aspect);

-- extraction_checkpoint indexes
CREATE INDEX IF NOT EXISTS idx_checkpoint_status ON extraction_checkpoint(status);
CREATE INDEX IF NOT EXISTS idx_checkpoint_review_id ON extraction_checkpoint(review_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_last_attempt ON extraction_checkpoint(last_attempt_time);

-- Composite index for checkpoint queries
CREATE INDEX IF NOT EXISTS idx_checkpoint_status_review ON extraction_checkpoint(status, review_id);

-- Index comments
COMMENT ON INDEX idx_entities_raw_entity_type IS 'Filters entities by type (12 types) for heritage categorization';
COMMENT ON INDEX idx_relations_raw_source_target IS 'Graph traversal queries between entities';
COMMENT ON INDEX idx_sentiments_raw_aspect_sentiment IS 'Aspect-sentiment analysis (e.g., all positive service sentiments)';
COMMENT ON INDEX idx_checkpoint_status IS 'Finds pending/failed reviews for incremental extraction';