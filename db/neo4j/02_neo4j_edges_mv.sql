-- ═══════════════════════════════════════════════════════════════════
-- NEO4J SYNC: neo4j_edges_mv
-- ═══════════════════════════════════════════════════════════════════
-- Materialized view aggregating canonical relations for Neo4j
-- ═══════════════════════════════════════════════════════════════════

DROP MATERIALIZED VIEW IF EXISTS neo4j_edges_mv CASCADE;

CREATE MATERIALIZED VIEW neo4j_edges_mv AS
SELECT
    source_entity_id::TEXT || '_' || target_entity_id::TEXT AS id,
    source_entity_id,
    target_entity_id,
    SUM(CASE WHEN relation_type = 'co_occurrence' THEN weight ELSE 0 END)::INTEGER AS co_occur_count,
    SUM(CASE WHEN relation_type IN ('causal', 'description', 'contrast') THEN weight ELSE 0 END)::INTEGER AS semantic_count,
    MAX(first_seen_year) AS first_seen_year,
    MAX(last_seen_year) AS last_seen_year,
    MAX(updated_at) AS updated_at
FROM relations
GROUP BY source_entity_id, target_entity_id;

-- Indexes for materialized view
CREATE UNIQUE INDEX idx_neo4j_edges_mv_src_tgt ON neo4j_edges_mv(source_entity_id, target_entity_id);
CREATE INDEX idx_neo4j_edges_mv_updated ON neo4j_edges_mv(updated_at);

-- Function to refresh it
CREATE OR REPLACE FUNCTION refresh_neo4j_mvs()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY neo4j_edges_mv;
END;
$$ LANGUAGE plpgsql;

COMMENT ON MATERIALIZED VIEW neo4j_edges_mv IS 'Aggregated relations for Neo4j synchronization, combining co-occurrence and semantic counts';
