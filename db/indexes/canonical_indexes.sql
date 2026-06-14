-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE INDEXES
-- ═══════════════════════════════════════════════════════════════════

-- entities
CREATE INDEX IF NOT EXISTS idx_entities_canonical_name ON entities(canonical_name);
CREATE INDEX IF NOT EXISTS idx_entities_entity_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_mention_count ON entities(mention_count DESC);

-- entity_aliases
CREATE INDEX IF NOT EXISTS idx_entity_aliases_entity_id ON entity_aliases(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_aliases_normalized ON entity_aliases(normalized_alias);
CREATE INDEX IF NOT EXISTS idx_entity_aliases_type_scope ON entity_aliases(entity_type, scope_type, scope_id);
CREATE INDEX IF NOT EXISTS idx_entity_aliases_confidence ON entity_aliases(confidence DESC);

-- entity_mentions
CREATE INDEX IF NOT EXISTS idx_entity_mentions_entity_id ON entity_mentions(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_mentions_review_id ON entity_mentions(review_id);

-- relations
CREATE INDEX IF NOT EXISTS idx_relations_source_entity ON relations(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relations_target_entity ON relations(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_relations_relation_type ON relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_relations_weight ON relations(weight DESC);

-- relation_mentions
CREATE INDEX IF NOT EXISTS idx_relation_mentions_relation_id ON relation_mentions(relation_id);
CREATE INDEX IF NOT EXISTS idx_relation_mentions_review_id ON relation_mentions(review_id);

-- sentiments
CREATE INDEX IF NOT EXISTS idx_sentiments_aspect ON sentiments(aspect);
CREATE INDEX IF NOT EXISTS idx_sentiments_mention_count ON sentiments(mention_count DESC);

-- sentiment_mentions
CREATE INDEX IF NOT EXISTS idx_sentiment_mentions_sentiment_id ON sentiment_mentions(sentiment_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_mentions_review_id ON sentiment_mentions(review_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_mentions_label ON sentiment_mentions(sentiment_label);

-- normalization tracking
CREATE INDEX IF NOT EXISTS idx_normalization_runs_status ON normalization_runs(status);
CREATE INDEX IF NOT EXISTS idx_normalization_checkpoints_raw ON normalization_checkpoints(raw_table, raw_id);
CREATE INDEX IF NOT EXISTS idx_normalization_checkpoints_status ON normalization_checkpoints(status);

COMMENT ON INDEX idx_relations_weight IS 'Ranks canonical graph edges by supporting mention count';
COMMENT ON INDEX idx_sentiment_mentions_label IS 'Filters positive, neutral, and negative aspect mentions';
