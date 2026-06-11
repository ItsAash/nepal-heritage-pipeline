-- ═══════════════════════════════════════════════════════════════════
-- CANONICAL TABLE: entity_mentions
-- ═══════════════════════════════════════════════════════════════════
-- Mention-level provenance for canonical entities.
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS entity_mentions (
    id                BIGSERIAL PRIMARY KEY,
    raw_entity_id     BIGINT UNIQUE NOT NULL,
    entity_id         BIGINT NOT NULL REFERENCES entities(id),
    review_id         TEXT NOT NULL,
    year              INTEGER,
    period            TEXT,
    trip_type         TEXT,
    rating            NUMERIC,
    entity_name_raw   TEXT NOT NULL,
    normalized_alias  TEXT NOT NULL,
    entity_type_raw   TEXT NOT NULL,
    quote             TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE entity_mentions
    ADD COLUMN IF NOT EXISTS normalized_alias TEXT NOT NULL DEFAULT '';

UPDATE entity_mentions
SET normalized_alias = lower(trim(regexp_replace(regexp_replace(entity_name_raw, '[[:punct:]]', ' ', 'g'), '[[:space:]]+', ' ', 'g')))
WHERE normalized_alias = '';

COMMENT ON TABLE entity_mentions IS 'One row per raw entity mention after canonical resolution. Preserves review-level provenance.';
COMMENT ON COLUMN entity_mentions.raw_entity_id IS 'entities_raw.id; unique to keep normalization rerunnable without duplicates';
COMMENT ON COLUMN entity_mentions.normalized_alias IS 'Python-normalized entity alias used during canonical resolution';
