# Changelog

## [Unreleased]

### Added
- Sprint 2: PostgreSQL docker-compose, Alembic migrations
- Unified SQLAlchemy session store (`sessions` table)
- PostgresSaver / MemorySaver checkpointer (auto by `DATABASE_URL`)
- E2E test: HITL survives graph reset (`test_escalation_survives_graph_reset`)
- `configure_database()` for test isolation
- Dev script tasks: `migrate`, `postgres`

### Changed
- Removed separate `sessions.db` — single database for app + dialog memory
- `session_store` uses SQLAlchemy via `app.database` module namespace

## [0.1.0] — 2026-06-08

### Added
- FastAPI + LangGraph support agent MVP
- SQLite: customers, orders, session memory
- Intents: order_status, account_info, general, complaint, unclear
- HITL escalation with interrupt/resume
- Mock LLM mode for offline development
