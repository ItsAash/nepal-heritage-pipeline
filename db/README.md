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

### Extraction Tables (Job 2 - LLM Extract)

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `entities_raw` | LLM-extracted entities | `review_id`, `entity_name`, `entity_type` (12 types), `quote` |
| `relations_raw` | Entity relations | `review_id`, `source_node`, `target_node`, `relation` (4 types) |
| `sentiments_raw` | Aspect sentiments | `review_id`, `aspect` (9 aspects), `sentiment`, `score`, `evidence` |
| `extraction_checkpoint` | Progress tracking | `review_id`, `status` (pending/processed/failed), `attempt_count` |

### Helper Functions

| Function | Purpose |
|----------|---------|
| `get_unprocessed_reviews(limit)` | Returns reviews not yet extracted (for incremental loading) |
| `update_checkpoint(id, status, error)` | Upserts extraction progress (used for resume capability) |

## Entity Types (12)
`scenic_spot`, `problem`, `facility_service`, `general_sentiment`, `ritual`, `religious_actor`, `sacred_space`, `spiritual_emotion`, `festival_event`, `cultural_rule`, `sacred_object`, `dual_valence`

## Relation Types (4)
`co_occurrence`, `causal`, `description`, `contrast`

## Sentiment Aspects (9)
`service`, `facility`, `environment`, `ritual_experience`, `spiritual_authenticity`, `access_fairness`, `sacred_atmosphere`, `crowd_management`, `cultural_sensitivity`

## Development Workflow

1. **Edit modular files** in `core/`, `extraction/`, `functions/`, `indexes/`
2. **Run builder** to generate unified schema
3. **Paste into Supabase** SQL Editor
4. **Never edit** `schema.sql` directly — it's generated

## Regenerating After Changes

```bash
# After any SQL file change:
python db/build_schema.py
# Paste into Supabase
```

## Gitignore
The generated `db/schema.sql` is in `.gitignore` — only modular source files are tracked.