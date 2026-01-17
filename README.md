# Korean News Recommendation Service

## Architecture Summary
- Airflow DAG runs 4x daily (Asia/Seoul) to ingest real Korean public-policy news sources, clean/normalize, deduplicate, extract keywords, assign topics, generate grounded newsletters, create embeddings, and update popularity.
- PostgreSQL + pgvector stores full lineage: articles → topics → newsletters → embeddings.
- FastAPI provides auth, personalized feed, popular topics, newsletter details with citations, and event logging.
- Next.js frontend offers signup/login, onboarding, feed, popular view, and newsletter detail with feedback controls.

## Assumptions
- Default sources are Korea.kr policy briefing RSS feeds with KOGL Type-1 license markers (verified by HTML pattern checks). See `services/backend/config/sources.yaml`.
- The pipeline only ingests sources flagged `allow_fulltext=true` and `allow_derivatives=true`, and can enforce per-source license patterns.
- Default embeddings use `intfloat/multilingual-e5-small` (384 dims). LLM uses OpenAI `gpt-4o-mini` when `OPENAI_API_KEY` is set.
- Embedding dimension is fixed to 384 in migrations; change requires a migration.
- If migrating from a previous 256-dim setup, recreate the DB volume or run the embedding-dimension migration.

## Local Run Guide

```bash
# Optional: copy defaults
cp .env.example .env

# Set required API keys for production-grade LLM
export OPENAI_API_KEY=...

# Build and start
docker compose up --build
```
If you have local port conflicts, set `POSTGRES_PORT`, `BACKEND_PORT`, `FRONTEND_PORT`, or `AIRFLOW_PORT` in `.env`.

Backend container runs Alembic migrations on startup.

### Trigger a DAG run
```bash
./scripts/trigger_dag.sh
# Or manually:
# docker compose exec airflow airflow dags trigger news_pipeline_daily_4x
```

### Create a user and view feed
- Frontend: open `http://localhost:3000` and use signup → onboarding → feed.
- Backend example:

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"strongpassword"}'
```

### Airflow UI
- `http://localhost:8080` (default credentials: `admin` / `admin` from `airflow standalone`).

## Pipeline Details
DAG: `news_pipeline_daily_4x`
- `fetch_articles`: per adapter, upsert articles with versioning (source registry in `services/backend/config/sources.yaml`)
- `clean_normalize`: clean text, language detect, data quality checks
- `deduplicate`: canonical URL + near-duplicate detection
- `extract_keywords`: TF-IDF + heuristic NER
- `assign_topics`: incremental topic assignment + merge
- `generate_newsletters`: real LLM grounded summary with citations (OpenAI/Anthropic, fallback to extractive)
- `embed_newsletters`: sentence-transformers embeddings into pgvector
- `update_popularity`: count of articles per topic

## ML / RecSys
### Phase 1 (implemented)
- User embedding from onboarding categories/keywords.
- PGVector retrieval + heuristic ranking (similarity + recency + popularity).
- Diversity via per-category/topic caps.
- Explainability returned in `reason` field.

### Phase 2 (runnable training)
- Offline training: `ml/training/train_phase2.py`
- Ranking model: Histogram gradient boosting classifier using similarity, recency, popularity, topic affinity, category/keyword match, rank position.
- User embeddings updated from positive interactions (click/save/follow).

#### Concrete training plan
- Model selection: two-tower retrieval (user embedding from interactions + preferences, item tower from newsletter text embedding) + lightweight ranker (hist gradient boosting; extensible to XGBoost/MLP).
- Pipeline: extract events + newsletter embeddings → label (click + dwell >= threshold or save/follow as positive, impression as negative) → time-based split → train ranker → update user embeddings.
- Default dwell threshold: 20 seconds (adjust in `ml/training/train_phase2.py`).
- Evaluation: Recall@K, NDCG@K, MAP@K, diversity/coverage per category; strict time split to avoid leakage.
- Online testing: A/B with guardrails (CTR, dwell, hide rate, diversity, source balance).

#### Train
```bash
PYTHONPATH=services/backend \
DATABASE_URL=postgresql+psycopg2://news:news_password@localhost:5432/news \
RANKER_MODEL_PATH=ml/artifacts/ranker.pkl \
python ml/training/train_phase2.py
```

#### Evaluate
```bash
PYTHONPATH=services/backend \
DATABASE_URL=postgresql+psycopg2://news:news_password@localhost:5432/news \
RANKER_MODEL_PATH=ml/artifacts/ranker.pkl \
python ml/evaluation/evaluate_offline.py
```
Outputs Recall@5, NDCG@5, MAP@5, Coverage@5, Diversity@5.

## Testing
- Unit tests: adapters, dedup, keyword extraction, topic thresholding, caching, auth, events.
- Integration test helper:
```bash
./scripts/integration_test.sh
```

To run tests against Postgres:
```bash
TEST_DATABASE_URL=postgresql+psycopg2://news:news_password@localhost:5432/news \
PYTHONPATH=services/backend \
pytest services/backend/tests
```

## Key Configuration Knobs
- `NEWS_SOURCES_FILE`, `NEWS_REQUEST_TIMEOUT`, `NEWS_MAX_ITEMS_PER_SOURCE`
- `TOPIC_SIMILARITY_THRESHOLD`, `TOPIC_MERGE_THRESHOLD`, `TOPIC_TIME_WINDOW_DAYS`
- `DEDUP_NEAR_THRESHOLD`
- `NEWSLETTER_MIN_BULLETS`, `NEWSLETTER_MAX_BULLETS`
- `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`
- `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `MOCK_LLM`
- `RANKER_MODEL_PATH`, `RANKER_META_PATH`
- `MMR_LAMBDA`, `MMR_MAX_CANDIDATES`
- `USER_EMBEDDING_DECAY_HOURS`
- `TIMEZONE` (default `Asia/Seoul`)

## Repo Structure
```
repo/
  docker-compose.yml
  .env.example
  README.md
  infra/
    airflow/
      dags/
      Dockerfile
  services/
    backend/
      app/
      tests/
      alembic/
      Dockerfile
    frontend/
      app/
      components/
      Dockerfile
  ml/
    training/
    evaluation/
  scripts/
```
