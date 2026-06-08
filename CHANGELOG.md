# Changelog

## [Unreleased]

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
