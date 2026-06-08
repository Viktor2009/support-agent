# Changelog

## [Unreleased]

## [1.5.0] — 2026-06-08 — Phase 6: full async API

### Added
- `async_admin.py`, `async_gdpr.py` — async DB for admin, GDPR, feedback, demo
- CI `staging` job: docker compose + smoke test
- `docs/TLS.md` — nginx TLS termination guide
- 3 unit tests for async admin/GDPR — 88 total

### Changed
- Admin, GDPR, `/chat/feedback`, `/demo/*` use async SQLAlchemy (no threadpool)

### Removed
- `app/executor.py` (`run_sync`) — no longer needed

## [1.4.1] — 2026-06-08

### Fixed
- Docker staging: `postgresql://` → `psycopg3` via `to_sync_database_url` / `to_psycopg_conninfo`
- Postgres checkpointer: setup with autocommit; `AsyncPostgresSaver` for `ainvoke`
- `service.py`: `aget_state` instead of sync `get_state` with async checkpointer

## [1.4.0] — 2026-06-08 — Phase 6: Production Hardening (start)

### Added
- Phase 6 roadmap (Production Hardening)
- `scripts/smoke_test.py` + `dev.ps1 -Task smoke`
- `.env.staging.example` for Postgres + Redis + auth staging profile
- Dependabot (pip + GitHub Actions)
- CI `audit` job: `pip-audit` on `requirements.txt`

### Changed
- `docker-compose.staging.yml`: `RATE_LIMIT_PER_MINUTE`, `METRICS_ENABLED`
- `docs/SECURITY.md`: staging profile checklist + smoke test instructions

## [1.3.1] — 2026-06-08

### Changed
- Ruff lint fixes (import order, line length, unused imports)
- README intro and project structure updated to match v1.3.0

### Removed
- Legacy sync `app/session_store.py` (replaced by `async_session_store`)

## [1.3.0] — 2026-06-08

### Added
- Async SQLAlchemy layer for graph DB access: `app/async_queries.py`, `app/async_session_store.py`
- `arun_tool` in tools registry; async tools registered at bootstrap
- Graph nodes `load_session`, `query_db`, `resolve_from_dialog`, `save_session` are `async def`
- `run_chat` / `stream_chat` / `resume_chat` use `graph.ainvoke` / `graph.astream` (no threadpool for graph)
- 3 new async query/session unit tests — 83 total

## [1.2.0] — 2026-06-08

### Added
- Live LLM token streaming in `/chat/stream` (LangGraph `custom` events from `synthesize_answer`)
- Prometheus `/metrics`: requests, escalations, latency histogram
- `MetricsMiddleware` on chat endpoints; `METRICS_ENABLED` config
- `/health` → `metrics` status
- 4 new tests — 80 total

## [1.1.0] — 2026-06-08

### Added
- RAG v2: embedding-based retrieval with hybrid keyword fallback
- Mock embeddings for offline/tests; OpenAI `text-embedding-3-small` when API key set
- Config: `RAG_MODE`, `RAG_USE_MOCK_EMBEDDINGS`, `EMBEDDING_MODEL`
- `/health` includes `rag` (mode, index type, chunk count)
- Hits include `retrieval_method` (`embedding` | `keyword`)
- 8 new RAG unit tests — 76 total

## [1.0.0] — 2026-06-08 — Production v1.0

### Added
- CI coverage gate (`--cov-fail-under=80`, currently ~86% on `app/`)
- CI load test job: 50 concurrent `/chat` sessions against live uvicorn
- CI golden dataset eval step
- `.\scripts\dev.ps1 -Task coverage`
- In-process concurrent chat smoke test (10 parallel)
- 1 new test — 68 total

## [0.7.0] — 2026-06-08

### Added
- Async API: all route handlers are `async def`; blocking graph/DB via threadpool
- Async DB layer (`asyncpg` for Postgres, `aiosqlite` for SQLite)
- `/health` includes `database_async` status
- Security headers middleware (`X-Request-ID`, `X-Content-Type-Options`, …)
- Operator guide: `docs/OPERATOR.md`
- Security checklist: `docs/SECURITY.md`
- 4 new tests — 65 total

## [0.6.0] — 2026-06-08

### Added
- SSE streaming: `POST /chat/stream` (node progress, token chunks, done/interrupt events)
- Widget uses streaming by default (`?stream=0` for classic `/chat`)
- Load test script (`scripts/load_test.py`, `.\scripts\dev.ps1 -Task loadtest`)
- Runbook: `docs/RUNBOOK.md`
- 2 new streaming integration tests — 61 total

## [0.5.0] — 2026-06-08

### Added
- Multi-tenant isolation (`tenant_id` on customers, orders, sessions, feedback)
- API keys: `tenant:customer:api_key` (legacy `customer:api_key` → tenant `default`)
- Supervisor node maps intent → agent (`active_agent` in chat response)
- Plugin tools registry (`app/tools/registry.py`, `bootstrap_tools()` on startup)
- GDPR endpoints: `GET /gdpr/sessions/{id}/export`, `DELETE /gdpr/sessions/{id}`
- PII masking for GDPR export (`mask_email`, `mask_pii_text`)
- Alembic migration `004_tenant_id`
- ACME tenant seed data for isolation tests
- 8 new tests — 59 total

## [0.4.0] — 2026-06-08

### Added
- Optional Redis cache + in-memory fallback (DB queries, intent classification)
- Rate limiting middleware (`RATE_LIMIT_PER_MINUTE`)
- `POST /chat/feedback` with persistence
- Admin API (`/admin/api/*`) and dashboard (`/admin-ui/`)
- Golden dataset eval pipeline (`tests/eval/`, `.\scripts\dev.ps1 -Task eval`)
- 7 new tests — 51 total

## [0.3.0] — 2026-06-08

### Added
- Intents: `order_list`, `billing`, `faq`
- RAG: `knowledge/faq.md` + keyword retriever + `search_knowledge` graph node
- Invoices table + billing queries
- Zendesk ticket creation on escalation (mock + real API)
- Chat widget at `/widget/`
- 12 new tests — 44 total

## [0.2.0] — 2026-06-08

### Added
- API Key auth (`X-API-Key` header, `API_KEYS` config)
- CORS whitelist (`CORS_ORIGINS`)
- Langfuse optional tracing (`LANGFUSE_*` env vars)
- Extended `/health` (database, checkpointer, auth, langfuse status)
- Dockerfile + `docker-compose.staging.yml`
- 8 new tests (auth, config, health) — 32 total

### Changed
- App version 0.2.0
- `customer_id` resolved from API key when auth enabled

## [0.1.0] — 2026-06-08

### Added
- FastAPI + LangGraph support agent MVP
- Test infrastructure, Alembic, PostgreSQL docker-compose
- Unified SQLAlchemy session store, PostgresSaver / MemorySaver
- HITL escalation with interrupt/resume
- Mock LLM mode for offline development
