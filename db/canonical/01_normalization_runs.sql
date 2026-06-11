-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: normalization_runs
-- ═══════════════════════════════════════════════════════════════════
-- Tracks standalone Gold Canonical normalization executions.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS normalization_runs (
    id                    BIGSERIAL PRIMARY KEY,
    started_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at           TIMESTAMP,
    status                TEXT NOT NULL DEFAULT 'running',
    entities_processed    INTEGER DEFAULT 0,
    relations_processed   INTEGER DEFAULT 0,
    sentiments_processed  INTEGER DEFAULT 0,
    error_message         TEXT,
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE normalization_runs IS 'Execution log for the standalone Gold Canonical normalization workflow.';
COMMENT ON COLUMN normalization_runs.status IS 'running | completed | failed';
