-- ═══════════════════════════════════════════════════════════════════
-- FUNCTION: get_unprocessed_reviews
-- ═══════════════════════════════════════════════════════════════════
-- Returns reviews from cleaned_reviews that have not been extracted yet
-- Used by: llm-extract/loader.py → get_unprocessed_reviews()
-- Called via: supabase.rpc("get_unprocessed_reviews", {limit_count: N})
-- ═══════════════════════════════════════════════════════════════════

DROP FUNCTION IF EXISTS get_unprocessed_reviews(limit_count INTEGER);

CREATE OR REPLACE FUNCTION get_unprocessed_reviews(limit_count INTEGER DEFAULT 1000)
RETURNS TABLE (
    review_id     TEXT,
    text_clean    TEXT,
    rating        NUMERIC,
    year          INTEGER,
    period        TEXT,
    trip_type     TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cr.review_id,
        cr.text_clean,
        cr.rating,
        cr.year,
        cr.period,
        cr.trip_type
    FROM cleaned_reviews cr
    LEFT JOIN extraction_checkpoint ec ON cr.review_id = ec.review_id
    WHERE ec.review_id IS NULL OR ec.status = 'pending'
    ORDER BY cr.ingested_at ASC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function comment
COMMENT ON FUNCTION get_unprocessed_reviews(INTEGER) IS 'Returns up to limit_count reviews that have not been extracted (status=NULL or pending). Orders by ingestion time for FIFO processing.';