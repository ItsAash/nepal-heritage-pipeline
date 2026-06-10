## Gold Layer Extraction Pipeline (Job 2)

Simple, readable, production-ready pipeline to extract semantic data from reviews.

### Overview

This pipeline transforms cleaned reviews into 3 raw tables:
- **entities_raw**: Review entities with types (scenic_spot, ritual, etc.)
- **relations_raw**: Relationships between entities
- **sentiments_raw**: Aspect-level sentiment analysis

### Architecture

```
cleaned_reviews (source)
    ↓
[FETCH] Get unprocessed reviews (checkpoint tracking)
    ↓
[CHUNK] Split into batches (45 reviews/batch)
    ↓
[EXTRACT] Submit to OpenAI Batch API → wait for completion
    ↓
[RECOVER] JSON parse/recovery (regex-based if needed)
    ↓
[TRANSFORM] Flatten JSON → 3 raw tables
    ↓
[LOAD] Batch insert to Supabase
    ↓
[CHECKPOINT] Mark as processed
```

### Modules

| Module | Purpose |
|--------|---------|
| `config.py` | Environment variables (OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY, MAX_REVIEWS_PER_RUN) |
| `prompt.py` | Build extraction prompt for LLM |
| `batch_handler.py` | OpenAI Batch API: chunking, submission, polling |
| `json_recovery.py` | Regex-based malformed JSON recovery |
| `transformer.py` | Transform LLM JSON → 3 raw tables |
| `loader.py` | Incremental loading + checkpoint tracking |
| `main.py` | Orchestration (fetch → extract → transform → load) |
| `schema.sql` | Database schema (3 raw tables + checkpoint) |
| `test_pipeline.py` | 10-record end-to-end test |

### Setup

#### 1. Create Database Tables

```bash
# Execute in Supabase SQL Editor
cat llm-extract/schema.sql | pbcopy
# Paste in SQL editor and execute
```

#### 2. Install Dependencies

```bash
pip install -r llm-extract/requirements.txt
```

#### 3. Set Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="eyJhbG..."
```

#### 4. Test (10 Records)

```bash
# Dry run (no API calls)
TEST_MODE=dry_run python llm-extract/test_pipeline.py

# Real test (calls OpenAI API, costs ~$0.008)
MAX_REVIEWS_PER_RUN=10 python llm-extract/main.py
```

### Usage

#### Extract All Unprocessed Reviews

```bash
python llm-extract/main.py
```

Reads env var `MAX_REVIEWS_PER_RUN` (default: 1,000,000).

#### Extract Limited Batch (Testing)

```bash
MAX_REVIEWS_PER_RUN=10 python llm-extract/main.py
```

### Incremental Loading & Checkpointing

The pipeline tracks progress in the `extraction_checkpoint` table:

| review_id | status | error_msg | attempt_count | last_attempt_time |
|-----------|--------|-----------|---------------|--------------------|
| rev_001 | processed | NULL | 1 | 2024-01-15 10:00:00 |
| rev_002 | failed | JSON parse error | 1 | 2024-01-15 10:01:00 |
| rev_003 | pending | NULL | 0 | NULL |

**On each run**:
1. Query `get_unprocessed_reviews()` → finds reviews with `status = pending` or missing checkpoint
2. Skip already-processed reviews (status = processed)
3. If extraction fails → store checkpoint with error
4. Next run will skip failed reviews (incremental loading)

### JSON Recovery Strategy

If LLM response is malformed:

1. **Direct JSON parsing** → try `json.loads()`
2. **Markdown extraction** → find `\`\`\`json ... \`\`\``
3. **Bare JSON extraction** → find `{...}` in response
4. **Regex reconstruction** → rebuild JSON using field patterns
5. **Fail & checkpoint** → store error, skip review

### Data Transformation

LLM returns:
```json
{
  "entities": [
    {"id": 1, "name": "pagoda", "type": "scenic_spot", "quote": "beautiful"}
  ],
  "relations": [
    {"from_id": 1, "to_id": 2, "type": "co_occurrence", "description": "..."}
  ],
  "aspect_sentiments": [
    {"aspect": "environment", "sentiment": "positive", "score": 0.9, "evidence": "..."}
  ],
  "review_type": "devotional",
  "dominant_experience": "Spiritual awakening"
}
```

Transforms to:
- **entities_raw**: review_id, year, period, trip_type, entity_name, entity_type, quote, rating
- **relations_raw**: review_id, year, source_node, target_node, relation, description
- **sentiments_raw**: review_id, year, trip_type, aspect, sentiment, score, evidence, rating

### Logging

All events logged to stderr as JSON (one per line):

```json
{"event": "batch_submitted", "batch_id": "batch_...", "review_count": 45}
{"event": "extraction_transformed", "review_id": "rev_001", "entity_count": 6}
{"event": "review_processed", "review_id": "rev_001", "entities": 6, "relations": 2}
{"event": "pipeline_complete", "total_processed": 45, "total_failed": 1}
```

Parse with:
```bash
python llm-extract/main.py 2>&1 | jq '.event'
```

### Monitoring

Query results in Supabase:

```sql
-- Check extraction progress
SELECT COUNT(*) as processed, 
       COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
FROM extraction_checkpoint;

-- View entities extracted
SELECT entity_type, COUNT(*) as count
FROM entities_raw
GROUP BY entity_type
ORDER BY count DESC;

-- Check recent errors
SELECT review_id, error_msg, last_attempt_time
FROM extraction_checkpoint
WHERE status = 'failed'
ORDER BY last_attempt_time DESC
LIMIT 10;
```

### Cost Estimates

- **10 reviews**: ~$0.008 (test)
- **100 reviews**: ~$0.08
- **1000 reviews**: ~$0.80
- **10,000 reviews**: ~$8.00

Uses OpenAI Batch API (50% discount vs standard API).

### Troubleshooting

**Issue**: "Missing required env vars"
- Set: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY

**Issue**: "Supabase connectivity failed"
- Verify SUPABASE_URL and SUPABASE_KEY are correct
- Check network connection

**Issue**: "Batch processing timeout"
- Default timeout: 3600s (1 hour)
- OpenAI may take 10-30 min for batch processing
- Check batch status: https://platform.openai.com/batches

**Issue**: "JSON parse failed for review X"
- Logged in checkpoint table with error message
- Review will be skipped on next run
- Manually inspect LLM output if needed

### Next Steps

1. Run schema.sql to create tables
2. Run test: `TEST_MODE=dry_run python test_pipeline.py`
3. Extract 10 reviews: `MAX_REVIEWS_PER_RUN=10 python llm-extract/main.py`
4. Verify results in Supabase
5. Extract all reviews: `python llm-extract/main.py`
6. Configure GitHub Actions for automated extraction
