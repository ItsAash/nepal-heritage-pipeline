-- ═══════════════════════════════════════════════════════════════════
-- FUNCTION: update_checkpoint
-- ═══════════════════════════════════════════════════════════════════
-- Updates or inserts extraction progress for a review
-- Used by: llm-extract/loader.py → mark_processed(), mark_failed()
-- Called via: supabase.rpc("update_checkpoint", {p_review_id, p_status, p_error_msg})
-- Status values: 'pending' | 'processed' | 'failed'
-- ═══════════════════════════════════════════════════════════════════

DROP FUNCTION IF EXISTS update_checkpoint(p_review_id TEXT, p_status TEXT, p_error_msg TEXT);

CREATE OR REPLACE FUNCTION update_checkpoint(
    p_review_id TEXT,
    p_status TEXT,
    p_error_msg TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO extraction_checkpoint (review_id, status, error_msg, attempt_count, last_attempt_time)
    VALUES (p_review_id, p_status, p_error_msg, 1, CURRENT_TIMESTAMP)
    ON CONFLICT (review_id) DO UPDATE SET
        status = p_status,
        error_msg = p_error_msg,
        attempt_count = extraction_checkpoint.attempt_count + 1,
        last_attempt_time = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Function comment
COMMENT ON FUNCTION update_checkpoint(TEXT, TEXT, TEXT) IS 'Upserts extraction progress. Increments attempt_count on each call. Use status=processed for success, status=failed with error_msg for errors.';