-- ═══════════════════════════════════════════════════════════════════
-- FUNCTION: refresh_canonical_aggregates
-- ═══════════════════════════════════════════════════════════════════
-- Recomputes canonical counts and year ranges from mention tables.
-- Safe to rerun after every normalization execution.
-- ═══════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION refresh_canonical_aggregates()
RETURNS VOID AS $$
BEGIN
    UPDATE entities e
    SET
        mention_count = stats.mention_count,
        first_seen_year = stats.first_seen_year,
        last_seen_year = stats.last_seen_year,
        updated_at = CURRENT_TIMESTAMP
    FROM (
        SELECT
            em.entity_id,
            COUNT(*)::INTEGER AS mention_count,
            MIN(cr.year) AS first_seen_year,
            MAX(cr.year) AS last_seen_year
        FROM entity_mentions em
        LEFT JOIN cleaned_reviews cr ON em.review_id = cr.review_id
        GROUP BY em.entity_id
    ) stats
    WHERE e.id = stats.entity_id;

    UPDATE entities e
    SET
        mention_count = 0,
        first_seen_year = NULL,
        last_seen_year = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE NOT EXISTS (
        SELECT 1 FROM entity_mentions em WHERE em.entity_id = e.id
    );

    UPDATE entity_aliases ea
    SET
        mention_count = stats.mention_count,
        last_seen_raw_id = stats.last_seen_raw_id,
        updated_at = CURRENT_TIMESTAMP
    FROM (
        SELECT
            entity_id,
            normalized_alias,
            entity_type_raw,
            COUNT(*)::INTEGER AS mention_count,
            MAX(raw_entity_id) AS last_seen_raw_id
        FROM entity_mentions
        GROUP BY entity_id, normalized_alias, entity_type_raw
    ) stats
    WHERE ea.entity_id = stats.entity_id
      AND ea.normalized_alias = stats.normalized_alias
      AND ea.entity_type = stats.entity_type_raw;

    UPDATE relations r
    SET
        weight = stats.weight,
        first_seen_year = stats.first_seen_year,
        last_seen_year = stats.last_seen_year,
        updated_at = CURRENT_TIMESTAMP
    FROM (
        SELECT
            rm.relation_id,
            COUNT(*)::INTEGER AS weight,
            MIN(cr.year) AS first_seen_year,
            MAX(cr.year) AS last_seen_year
        FROM relation_mentions rm
        LEFT JOIN cleaned_reviews cr ON rm.review_id = cr.review_id
        GROUP BY rm.relation_id
    ) stats
    WHERE r.id = stats.relation_id;

    UPDATE relations r
    SET
        weight = 0,
        first_seen_year = NULL,
        last_seen_year = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE NOT EXISTS (
        SELECT 1 FROM relation_mentions rm WHERE rm.relation_id = r.id
    );

    UPDATE sentiments s
    SET
        positive_count = stats.positive_count,
        neutral_count = stats.neutral_count,
        negative_count = stats.negative_count,
        mention_count = stats.mention_count,
        avg_sentiment_score = stats.avg_sentiment_score,
        first_seen_year = stats.first_seen_year,
        last_seen_year = stats.last_seen_year,
        updated_at = CURRENT_TIMESTAMP
    FROM (
        SELECT
            sm.sentiment_id,
            COUNT(*) FILTER (WHERE sm.sentiment_label = 'positive')::INTEGER AS positive_count,
            COUNT(*) FILTER (WHERE sm.sentiment_label = 'neutral')::INTEGER AS neutral_count,
            COUNT(*) FILTER (WHERE sm.sentiment_label = 'negative')::INTEGER AS negative_count,
            COUNT(*)::INTEGER AS mention_count,
            AVG(sm.sentiment_score) AS avg_sentiment_score,
            MIN(cr.year) AS first_seen_year,
            MAX(cr.year) AS last_seen_year
        FROM sentiment_mentions sm
        LEFT JOIN cleaned_reviews cr ON sm.review_id = cr.review_id
        GROUP BY sm.sentiment_id
    ) stats
    WHERE s.id = stats.sentiment_id;

    UPDATE sentiments s
    SET
        positive_count = 0,
        neutral_count = 0,
        negative_count = 0,
        mention_count = 0,
        avg_sentiment_score = NULL,
        first_seen_year = NULL,
        last_seen_year = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE NOT EXISTS (
        SELECT 1 FROM sentiment_mentions sm WHERE sm.sentiment_id = s.id
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_canonical_aggregates() IS 'Recomputes canonical entity, relation, and aspect sentiment aggregates from mention tables.';
