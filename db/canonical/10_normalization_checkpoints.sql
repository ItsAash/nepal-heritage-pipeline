-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: normalization_checkpoints
-- ═══════════════════════════════════════════════════════════════════
-- Tracks raw rows processed by the standalone canonical workflow without
-- mutating entities_raw, relations_raw, or sentiments_raw.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS normalization_checkpoints (
    id             BIGSERIAL PRIMARY KEY,
    raw_table      TEXT NOT NULL,
    raw_id         BIGINT NOT NULL,
    run_id         BIGINT REFERENCES normalization_runs(id),
    status         TEXT NOT NULL DEFAULT 'processed',
    error_message  TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_table, raw_id)
);

COMMENT ON TABLE normalization_checkpoints IS 'Canonical normalization progress keyed by raw table and raw row ID. Raw tables remain immutable.';
COMMENT ON COLUMN normalization_checkpoints.raw_table IS 'entities_raw | relations_raw | sentiments_raw';
