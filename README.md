# Support Agent — FastAPI + LangGraph

Production-ready support agent на **FastAPI + LangGraph**: БД, RAG, HITL-эскалация, multi-tenant, SSE streaming, admin panel и Prometheus metrics.

## Быстрый старт

```powershell
cd c:\AI_pom\support-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Для локального теста без OpenAI API:

```env
MOCK_LLM=true
```

Запуск:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Если порт 8000 занят (Docker, старый uvicorn):

```powershell
# Посмотреть, кто держит порт
netstat -ano | findstr ":8000"

# Или запустить на другом порту
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Swagger: http://127.0.0.1:8000/docs (или :8080)

## Admin panel

```
http://127.0.0.1:8000/admin-ui/
# Header: X-Admin-Key (set ADMIN_API_KEY in .env)
```

API: `/admin/api/stats`, `/admin/api/sessions`, `/admin/api/escalations`, `/admin/api/feedback`

## Feedback

```powershell
curl -X POST http://127.0.0.1:8000/chat/feedback `
  -H "Content-Type: application/json" `
  -d '{"session_id":"s1","rating":5,"customer_id":"cust_456","comment":"Отлично"}'
```

## Eval pipeline

```powershell
.\scripts\dev.ps1 -Task eval
```

## Chat widget

```
http://127.0.0.1:8000/widget/?customer_id=cust_456
# SSE streaming по умолчанию; ?stream=0 — классический POST /chat
```

## SSE streaming (v0.6.0)

```powershell
curl -N -X POST http://127.0.0.1:8000/chat/stream `
  -H "Content-Type: application/json" `
  -d '{"session_id":"s1","message":"Где мой заказ #1?","customer_id":"cust_456"}'
```

События: `node` (прогресс графа), `token` (live из `synthesize_answer` или чанки), `done`, `interrupt`.

## Metrics (v1.2.0)

```
GET /metrics   # Prometheus format (METRICS_ENABLED=true)
```

Счётчики: `support_chat_requests_total`, `support_chat_escalations_total`, histogram `support_chat_duration_seconds`.

## Load test

```powershell
.\scripts\dev.ps1 -Task run      # в отдельном терминале
.\scripts\dev.ps1 -Task loadtest # 50 concurrent /chat
```

Runbook: [docs/RUNBOOK.md](docs/RUNBOOK.md)  
Operator guide: [docs/OPERATOR.md](docs/OPERATOR.md)  
Security checklist: [docs/SECURITY.md](docs/SECURITY.md)

## Async API (v1.3.0)

Все эндпоинты — `async def`. LangGraph (`ainvoke` / `astream`) и DB-узлы графа — async SQLAlchemy (`aiosqlite` / `asyncpg`).  
Admin, GDPR и demo-эндпоинты по-прежнему используют sync ORM через threadpool.  
`/health` возвращает `database_async` (asyncpg / aiosqlite).

## Новые intents (v0.3.0)

| Intent | Пример |
|--------|--------|
| `order_list` | «Покажи все мои заказы» |
| `billing` | «Какие у меня счета?» |
| `faq` | «Какая политика возврата?» |

FAQ отвечает из `knowledge/faq.md` (hybrid RAG: embeddings + keyword fallback).

## RAG v2 (v1.1.0)

По умолчанию `RAG_MODE=auto`: mock-embeddings при `MOCK_LLM=true`, OpenAI embeddings в production.

```env
RAG_MODE=auto          # auto | keyword | embedding
RAG_USE_MOCK_EMBEDDINGS=true
EMBEDDING_MODEL=text-embedding-3-small
```

`/health` → `rag.mode`, `rag.chunks`.

## Staging (Docker)

```powershell
docker compose -f docker-compose.staging.yml up --build
# API: http://127.0.0.1:8000/docs
# Header: X-API-Key: staging-key-cust456
```

## Auth (API Key)

Когда `API_KEYS` задан в `.env`, все `/chat` и `/demo` эндпоинты требуют заголовок:

```
X-API-Key: your-key
```

Формат `.env`:
- Legacy: `API_KEYS=cust_456:key-for-456` (tenant = `default`)
- Multi-tenant: `API_KEYS=default:cust_456:key1,acme:cust_acme:key2`

`customer_id` и `tenant_id` берутся из ключа — передавать в body необязательно.

## Multi-tenant (v0.5.0)

Ответ `/chat` включает `tenant_id` и `active_agent` (supervisor: orders/billing/knowledge/general).

Демо-тенант `acme` с `cust_acme` и заказом #4 — для проверки изоляции.

## GDPR

```powershell
# Экспорт сессии (PII маскируется по умолчанию)
curl "http://127.0.0.1:8000/gdpr/sessions/s1/export?customer_id=cust_456"

# Удаление сессии и связанного feedback
curl -X DELETE "http://127.0.0.1:8000/gdpr/sessions/s1?customer_id=cust_456"
```

## PostgreSQL (production-like)

```powershell
.\scripts\dev.ps1 -Task postgres   # docker compose up -d
copy .env.example .env
# DATABASE_URL=postgresql://support:support@localhost:5432/support_agent
.\scripts\dev.ps1 -Task migrate
.\scripts\dev.ps1 -Task run
```

## Тесты и lint

```powershell
pip install -r requirements-dev.txt
$env:MOCK_LLM = "true"
pytest -v
ruff check app tests
```

Или через скрипт:

```powershell
.\scripts\dev.ps1 -Task test
.\scripts\dev.ps1 -Task coverage   # pytest + ≥80% coverage gate
.\scripts\dev.ps1 -Task lint
```

## Roadmap

План развития: [docs/ROADMAP.md](docs/ROADMAP.md)

## Демо-данные

| customer_id | order_id | status |
|---|---|---|
| cust_456 | 1 | shipped (delivery 2025-06-10) |
| cust_456 | 2 | processing |
| cust_789 | 3 | delivered |
| acme / cust_acme | 4 | shipped (tenant isolation demo) |

## Примеры запросов

### Статус заказа

```powershell
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"session_id":"s1","message":"Где мой заказ #1?","customer_id":"cust_456"}'
```

### Контекст из диалога (order_id из прошлого сообщения)

```powershell
# Шаг 1
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"session_id":"s2","message":"Привет, у меня вопрос по заказу #1","customer_id":"cust_456"}'

# Шаг 2 — без номера заказа, агент берёт из summary
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"session_id":"s2","message":"Когда доставка?","customer_id":"cust_456"}'
```

### Аккаунт

```powershell
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"session_id":"s3","message":"Какой у меня тариф и баланс?","customer_id":"cust_456"}'
```

### Escalation (жалоба)

```powershell
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"session_id":"s4","message":"Хочу возврат, сервис ужасный!","customer_id":"cust_456"}'
```

Ответ: `status: awaiting_operator` — граф на паузе (HITL).

### Resume оператором

```powershell
curl -X POST http://127.0.0.1:8000/chat/resume `
  -H "Content-Type: application/json" `
  -d '{"session_id":"s4","operator_reply":"Передаю менеджеру, вернёмся в течение 24ч","ticket_id":"ZD-001"}'
```

## Архитектура

```
POST /chat
    → load_session
    → classify_intent
    → supervisor (intent → agent)
    → check_escalation
    → query_db (tools registry) / search_knowledge / clarify / escalate
    → synthesize_answer
    → validate_answer
    → save_session

POST /chat/stream — тот же граф, ответ через SSE (node → token → done)
```

## Структура

```
support-agent/
├── app/
│   ├── main.py                 # FastAPI endpoints
│   ├── service.py              # ainvoke / astream graph
│   ├── database.py             # sync ORM (admin, GDPR, demo)
│   ├── async_queries.py        # async DB queries for graph nodes
│   ├── async_session_store.py  # async dialog memory
│   ├── rag/                    # embedding + keyword retriever
│   ├── tools/                  # plugin tools registry
│   ├── prompts/                # YAML prompt templates
│   └── graph/
│       ├── state.py
│       ├── nodes.py
│       ├── supervisor.py
│       └── builder.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── eval/                   # golden dataset
├── docs/
│   ├── ROADMAP.md
│   ├── RUNBOOK.md
│   ├── OPERATOR.md
│   └── SECURITY.md
├── scripts/
│   ├── dev.ps1
│   └── load_test.py
├── requirements.txt
└── .env.example
```

## Production next steps

- Postgres вместо SQLite
- Redis для sessions
- PostgresSaver для LangGraph checkpointing
- Langfuse / LangSmith для traces
- WebSocket streaming для chat widget
