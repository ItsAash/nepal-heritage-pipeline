-- ═══════════════════════════════════════════════════════════════════
-- NEO4J SYNC: neo4j_sync_checkpoints
-- ═══════════════════════════════════════════════════════════════════
-- Tracks incremental sync progress for Neo4j exports
-- ═══════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS neo4j_sync_checkpoints CASCADE;

CREATE TABLE neo4j_sync_checkpoints (
    table_name          TEXT PRIMARY KEY,
    last_synced_at      TIMESTAMP DEFAULT '1970-01-01 00:00:00',
    last_synced_id      TEXT DEFAULT '',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE neo4j_sync_checkpoints IS 'Tracks incremental sync progress for Neo4j exports';
