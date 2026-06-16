"""
Cypher Queries for Neo4j Sync
"""

# Constraints setup
SETUP_CONSTRAINTS = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Review) REQUIRE r.review_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Aspect) REQUIRE a.aspect IS UNIQUE"
]

# Sync Entities
SYNC_ENTITIES = """
UNWIND $batch AS row
MERGE (e:Entity {entity_id: row.id})
SET e.canonical_name = row.canonical_name,
    e.display_name = row.display_name,
    e.entity_type = row.entity_type,
    e.mention_count = row.mention_count,
    e.first_seen_year = row.first_seen_year,
    e.last_seen_year = row.last_seen_year
"""

# Sync Reviews
SYNC_REVIEWS = """
UNWIND $batch AS row
MERGE (r:Review {review_id: row.review_id})
SET r.title_clean = row.title_clean,
    r.text_clean = row.text_clean,
    r.rating = row.rating,
    r.sentiment_class = row.sentiment_class,
    r.year = row.year,
    r.period = row.period,
    r.trip_type = row.trip_type,
    r.reviewer_type = row.reviewer_type,
    r.language = row.language
"""

# Sync Sentiments (Aspects)
SYNC_SENTIMENTS = """
UNWIND $batch AS row
MERGE (a:Aspect {aspect: row.aspect})
SET a.aspect_id = row.id,
    a.display_aspect = row.display_aspect,
    a.mention_count = row.mention_count,
    a.avg_sentiment_score = row.avg_sentiment_score
"""

# Sync Entity Mentions
SYNC_ENTITY_MENTIONS = """
UNWIND $batch AS row
MATCH (r:Review {review_id: row.review_id})
MATCH (e:Entity {entity_id: row.entity_id})
MERGE (r)-[m:MENTIONS]->(e)
SET m.quote = row.quote
"""

# Sync Sentiment Mentions
SYNC_SENTIMENT_MENTIONS = """
UNWIND $batch AS row
MATCH (r:Review {review_id: row.review_id})
MATCH (a:Aspect {aspect_id: row.sentiment_id})
MERGE (r)-[expr:EXPRESSES_SENTIMENT]->(a)
SET expr.sentiment_label = row.sentiment_label,
    expr.sentiment_score = row.sentiment_score,
    expr.evidence = row.evidence
"""

# Sync Neo4j Edges
SYNC_NEO4J_EDGES = """
UNWIND $batch AS row
MATCH (src:Entity {entity_id: row.source_entity_id})
MATCH (tgt:Entity {entity_id: row.target_entity_id})
MERGE (src)-[rel:RELATED_TO]->(tgt)
SET rel.weight = row.weight,
    rel.co_occur_count = row.co_occur_count,
    rel.semantic_count = row.semantic_count,
    rel.first_seen_year = row.first_seen_year,
    rel.last_seen_year = row.last_seen_year
"""
