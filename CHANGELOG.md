# Changelog

## [Unreleased]

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
