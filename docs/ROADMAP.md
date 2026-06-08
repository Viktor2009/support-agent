# Roadmap — Support Agent

> Зафиксирован: 2026-06-08 · Текущая версия API: 0.6.0

## Цели

| Цель | Метрика |
|------|---------|
| Снизить нагрузку на операторов | ≥40% запросов без эскалации |
| Ускорить ответ | p95 < 5 с |
| Качество grounding | ≥90% ответов подтверждены evidence |
| Безопасность | 0 утечек чужих данных |

## Принципы

1. **Grounding first** — факты только из БД / RAG / tools.
2. **Граф как оркестратор** — логика в узлах LangGraph.
3. **HITL first-class** — эскалация штатный путь.
4. **Observability с production** — каждый шаг трассируется.

---

## Фаза 0 — Инженерная база (неделя 1) `[DONE]`

- [x] ROADMAP.md
- [x] Git + структура репозитория
- [x] pyproject.toml, requirements-dev, ruff
- [x] Каркас tests/ (23 теста: unit + integration)
- [x] GitHub Actions CI
- [x] Промпты в app/prompts/
- [x] CHANGELOG.md

## Фаза 1 — Production foundation (недели 2–4) `[DONE]`

- [x] PostgreSQL docker-compose
- [x] Alembic миграции (customers, orders, sessions)
- [x] Session store → SQLAlchemy (единая БД)
- [x] PostgresSaver / MemorySaver (auto по DATABASE_URL)
- [x] E2E тест: эскалация → reset graph → resume
- [x] API Key auth, customer_id из токена
- [x] CORS whitelist (configurable)
- [x] Langfuse callbacks (optional)
- [x] Dockerfile + docker-compose.staging
- [x] Расширенный /health
- [x] Rate limiting

## Фаза 2 — Pilot (недели 5–8) `[DONE]`

- [x] Новые intents: order_list, billing, faq
- [x] RAG: knowledge/ + search_knowledge node
- [x] Zendesk integration при эскалации (mock + real API)
- [x] Chat widget (MVP) — `/widget/`
- [x] SSE streaming (`POST /chat/stream`, widget)

## Фаза 3 — Масштабирование (недели 9–14) `[DONE]`

- [x] Redis cache (optional) + in-memory fallback
- [x] Rate limiting (per IP)
- [x] Eval pipeline (golden dataset, ≥85% intent accuracy)
- [x] Feedback endpoint (`POST /chat/feedback`)
- [x] Admin panel (`/admin-ui/`) + API (`/admin/api/*`)
- [ ] Async API + asyncpg

## Фаза 4 — Платформа (недели 15–24) `[DONE]`

- [x] Multi-tenant (`tenant_id`, API key format `tenant:customer:key`)
- [x] Multi-agent supervisor (`active_agent` in response)
- [x] Plugin tools registry
- [x] GDPR: delete/export sessions, PII masking

---

## Sprint 1 (дни 1–5) — завершён

- [x] Git init
- [x] 23 unit/integration теста (mock LLM)
- [x] GitHub Actions: lint + test
- [x] Промпты → app/prompts/intent.yaml

## Sprint 2 (дни 6–10) — завершён

- [x] Docker Compose + PostgreSQL
- [x] Alembic initial migration
- [x] Session store → SQLAlchemy (таблица `sessions`)
- [x] PostgresSaver / MemorySaver checkpointer
- [x] E2E тест HITL после reset graph (24 теста)

## Sprint 3 (дни 11–14) — завершён

- [x] API Key middleware (`X-API-Key` → customer_id)
- [x] Langfuse integration (optional callbacks)
- [x] Расширенный /health
- [x] Dockerfile + docker-compose.staging.yml
- [x] 32 автотеста

## Sprint 4 — завершён (Фаза 2)

- [x] Intents: order_list, billing, faq
- [x] RAG keyword retriever + `knowledge/faq.md`
- [x] Zendesk mock/real ticket on escalation
- [x] Chat widget at `/widget/`
- [x] 44 автотеста

## Sprint 5 — завершён (Фаза 3)

- [x] Cache layer (memory / Redis)
- [x] Rate limiting middleware
- [x] Feedback + admin API + admin UI
- [x] Golden dataset eval (51 tests)

## Sprint 6 — завершён (Production readiness)

- [x] SSE streaming endpoint + widget
- [x] Load test script (50 concurrent sessions)
- [x] Runbook (`docs/RUNBOOK.md`)
- [ ] Async API + asyncpg

## Definition of Done — Production v1.0

1. Все Must have (Фаза 0–2) выполнены
2. ≥30 автотестов, coverage критических путей ≥80%
3. Load test: 50 concurrent sessions
4. Runbook: деплой, откат, LLM down
5. Golden dataset eval проходит пороги
6. Security review пройден
7. Документация API + onboarding оператора
