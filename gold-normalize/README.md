## Gold Canonical Normalization Workflow

This standalone workflow reads existing Gold staging tables:

- `entities_raw`
- `relations_raw`
- `sentiments_raw`

It writes canonical tables:

- `entities`
- `entity_aliases`
- `entity_alias_candidates`
- `relations`
- `sentiments`
- `entity_mentions`
- `relation_mentions`
- `sentiment_mentions`

Raw staging tables are never mutated. Progress is tracked in `normalization_checkpoints`.

### Alias Learning

Entity aliasing is learned over time:

- `entity_aliases` stores approved mappings from raw labels to canonical entities.
- `entity_alias_candidates` stores medium-confidence suggestions for review.
- There is no static alias dictionary. `aliases.py` only contains generic lexical token classes used by the automatic matcher.

Resolution policy:

```text
learned alias match
  -> use approved canonical entity

exact canonical label match
  -> use canonical entity and persist alias

automatic token-subset match
  -> auto-link labels like "Bagmati" and "Bagmati River" when the extra tokens are generic descriptors/types

fuzzy score >= AUTO_ALIAS_THRESHOLD
  -> auto-link and persist alias

CANDIDATE_ALIAS_THRESHOLD <= fuzzy score < AUTO_ALIAS_THRESHOLD
  -> create/use separate canonical entity and queue merge candidate

fuzzy score < CANDIDATE_ALIAS_THRESHOLD
  -> create new canonical entity
```

To approve a queued candidate:

```sql
UPDATE entity_alias_candidates
SET status = 'approved'
WHERE id = <candidate_id>;
```

The next normalization run promotes approved candidates into `entity_aliases` with `source = 'manual'`.

Default thresholds:

```text
AUTO_ALIAS_THRESHOLD=95
CANDIDATE_ALIAS_THRESHOLD=75
```

### Run

```bash
python3 gold-normalize/main.py
```

### Reprocess Existing Raw Rows

Use this after changing aliases or normalization logic:

```bash
python3 gold-normalize/main.py --include-processed
```

Mention tables are upserted by raw row ID, and aggregate counts are recomputed from mention tables, so reruns are idempotent.
