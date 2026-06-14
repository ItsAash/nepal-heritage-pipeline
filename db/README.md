# Trip_Advisor Database Schema

Centralized database schema for the LLM-SC Pashupatinath Heritage Intelligence Platform.

## Structure

```
db/
├── core/                 # Job 1 (Scraper) tables
│   ├── 01_cleaned_reviews.sql
│   └── 02_scrape_runs.sql
├── extraction/           # Job 2 (LLM Extract) tables
│   ├── 01_entities_raw.sql
│   ├── 02_relations_raw.sql
│   ├── 03_sentiments_raw.sql
│   └── 04_extraction_checkpoint.sql
├── canonical/            # Job 3 (Gold Canonical Normalize) tables
│   ├── 01_normalization_runs.sql
│   ├── 02_entities.sql
│   ├── 03_entity_aliases.sql
│   ├── 05_entity_mentions.sql
│   ├── 06_relations.sql
│   ├── 07_relation_mentions.sql
│   ├── 08_sentiments.sql
│   ├── 09_sentiment_mentions.sql
│   └── 10_normalization_checkpoints.sql
├── functions/            # PostgreSQL functions
│   ├── 01_get_unprocessed_reviews.sql
│   └── 02_update_checkpoint.sql
├── indexes/              # Performance indexes
│   ├── core_indexes.sql
│   └── extraction_indexes.sql
├── build_schema.py       # Schema builder script
└── schema.sql            # Generated (gitignored)
```

## Quick Start

### 1. Install dependencies
```bash
pip install pyperclip  # Optional, for clipboard support
```

### 2. Build and copy to clipboard
```bash
python db/build_schema.py
# ✓ Schema copied to clipboard
```
Then paste directly into **Supabase SQL Editor**.

### 3. Alternative: Write to file
```bash
python db/build_schema.py --write
# Creates db/schema.sql for review
```

### 4. Validate without output
```bash
python db/build_schema.py --validate
# ✓ All 10 schema files present
```

## Table Overview

### Core Tables (Job 1 - Scraper)

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `cleaned_reviews` | Main review storage | `review_id` (PK), `text_clean`, `rating`, `year`, `period`, `trip_type`, sacred flags |
| `scrape_runs` | Scrape execution tracking | `run_id`, `total_reviews`, `new_reviews`, `run_date` |

### Extraction Tables (Job 2 - LLM Extract / Gold Staging)

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `entities_raw` | LLM-extracted entities | `review_id`, `entity_name`, `entity_type` (12 types), `quote` |
| `relations_raw` | Entity relations | `review_id`, `source_node`, `target_node`, `relation` (4 types) |
| `sentiments_raw` | Aspect sentiments | `review_id`, `aspect` (9 aspects), `sentiment`, `score`, `evidence` |
| `extraction_checkpoint` | Progress tracking | `review_id`, `status` (pending/processed/failed), `attempt_count` |

### Canonical Tables (Job 3 - Gold Canonical Normalize)

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `entities` | Canonical deduplicated entity nodes | `canonical_name`, `display_name`, `entity_type`, `mention_count` |
| `entity_aliases` | Approved learned aliases and candidates | `normalized_alias`, `entity_id`, `status`, `confidence`, `scope_type` |
| `relations` | Canonical weighted graph edges | `source_entity_id`, `target_entity_id`, `relation_type`, `weight` |
| `sentiments` | Canonical aspect-level sentiment aggregates | `aspect`, `positive_count`, `neutral_count`, `negative_count`, `avg_sentiment_score` |
| `entity_mentions` | Review-level entity provenance | `raw_entity_id`, `entity_id`, `review_id`, temporal/trip metadata |
| `relation_mentions` | Review-level relation provenance | `raw_relation_id`, `relation_id`, `review_id`, temporal/trip metadata |
| `sentiment_mentions` | Review-level aspect sentiment provenance | `raw_sentiment_id`, `sentiment_id`, `review_id`, `sentiment_label`, `sentiment_score` |
| `normalization_runs` | Standalone canonical workflow runs | `status`, processed counts, timestamps |
| `normalization_checkpoints` | Raw-row normalization progress | `raw_table`, `raw_id`, `status` |

Raw staging tables are immutable. The canonical workflow tracks progress through `normalization_checkpoints` and uses raw-row unique keys on mention tables for idempotent reruns.

### Helper Functions

| Function | Purpose |
|----------|---------|
| `get_unprocessed_reviews(limit)` | Returns reviews not yet extracted (for incremental loading) |
| `update_checkpoint(id, status, error)` | Upserts extraction progress (used for resume capability) |
| `refresh_canonical_aggregates()` | Recomputes canonical entity, relation, and aspect sentiment aggregates from mention tables |

## Entity Types (12)
`scenic_spot`, `problem`, `facility_service`, `general_sentiment`, `ritual`, `religious_actor`, `sacred_space`, `spiritual_emotion`, `festival_event`, `cultural_rule`, `sacred_object`, `dual_valence`

## Relation Types (4)
`co_occurrence`, `causal`, `description`, `contrast`

## Sentiment Aspects (9)
`service`, `facility`, `environment`, `ritual_experience`, `spiritual_authenticity`, `access_fairness`, `sacred_atmosphere`, `crowd_management`, `cultural_sensitivity`

## Development Workflow

1. **Edit modular files** in `core/`, `extraction/`, `functions/`, `indexes/`
2. **Run builder** to generate unified non-destructive schema
3. **Paste into Supabase** SQL Editor
4. **Never edit** `schema.sql` directly — it's generated

## Regenerating After Changes

```bash
# After any SQL file change:
python db/build_schema.py
# Paste into Supabase
```

The generated schema omits destructive `DROP` statements and emits idempotent table/index creation, so it can be applied without deleting existing Supabase data.

## Gitignore
The generated `db/schema.sql` is in `.gitignore` — only modular source files are tracked.
