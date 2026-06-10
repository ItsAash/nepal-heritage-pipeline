-- ═══════════════════════════════════════════════════════════════════
-- EXTRACTION TABLE: extraction_checkpoint
-- ═══════════════════════════════════════════════════════════════════
-- Progress tracking for Job 2 extraction pipeline
-- Source: llm-extract/loader.py → mark_processed(), mark_failed()
-- Status values: 'pending' | 'processed' | 'failed'
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS extraction_checkpoint CASCADE;

CREATE TABLE extraction_checkpoint (
    id                  BIGSERIAL PRIMARY KEY,
    review_id           TEXT UNIQUE NOT NULL,
    status              TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'processed' | 'failed'
    error_msg           TEXT,
    attempt_count       INTEGER DEFAULT 0,
    last_attempt_time   TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table comment
COMMENT ON TABLE extraction_checkpoint IS 'Tracks extraction progress per review. Enables incremental loading and resumability.';

-- Column comments
COMMENT ON COLUMN extraction_checkpoint.status IS 'pending=not yet processed, processed=successfully extracted, failed=extraction error';
COMMENT ON COLUMN extraction_checkpoint.error_msg IS 'Error message if status=failed (truncated to 500 chars)';
COMMENT ON COLUMN extraction_checkpoint.attempt_count IS 'Number of extraction attempts';
COMMENT ON COLUMN extraction_checkpoint.last_attempt_time IS 'Timestamp of last extraction attempt';