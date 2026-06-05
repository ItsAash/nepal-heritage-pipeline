## TripAdvisor Pashupatinath Pipeline

### What It Does
Scrapes TripAdvisor reviews for Pashupatinath Temple every 15 days, cleans them, and stores in Supabase PostgreSQL.

### Architecture
```
GitHub Actions (cron) → Scraper → Cleaner → Supabase PostgreSQL
```

### Files

| File | Purpose |
|---|---|
| `scraper/scraper.py` | Scrapes TripAdvisor API (198 pages) |
| `scraper/validate.py` | Checks data quality |
| `scraper/clean_and_upload.py` | Cleans raw data, inserts into Supabase |

### How to Change Things

| Want to change... | Edit this |
|---|---|
| Scrape frequency | `.github/workflows/scrape-tripadvisor.yml` → `cron` |
| Temple/location | `scraper/scraper.py` → `QUERY` |
| API key | GitHub Settings → Secrets → `API_KEY` |
| Supabase database | GitHub Settings → Secrets → `SUPABASE_URL`, `SUPABASE_KEY` |
| Cleaning logic | `scraper/clean_and_upload.py` |
| Columns in database | `clean_and_upload.py` + Supabase SQL Editor |

### Running Manually
GitHub → Actions → "Scrape Pashupatinath Reviews" → Run workflow

### Database Tables
- `cleaned_reviews` — all cleaned review data
- `scrape_runs` — metadata for each run

### Adding New Columns
1. Add column in `clean_and_upload.py` → `record` dict
2. Run `ALTER TABLE cleaned_reviews ADD COLUMN new_col TYPE;` in Supabase SQL Editor
3. Push and re-run workflow

### Tech Stack
- Python 3.11
- GitHub Actions
- Supabase (PostgreSQL)
- TripAdvisor Scraper API (omkar.cloud)

---

