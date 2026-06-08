# Support Agent — FastAPI + LangGraph

Минимальный support agent: **БД (SQLite) + живой диалог**, без RAG/файлов.

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

Формат `.env`: `API_KEYS=cust_456:key-for-456,cust_789:key-for-789`  
`customer_id` берётся из ключа — передавать в body необязательно.

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
    → load_session (SQLite sessions)
    → classify_intent
    → check_escalation
    → query_db / clarify / escalate / synthesize
    → validate_answer
    → save_session
```

## Структура

```
support-agent/
├── app/
│   ├── main.py           # FastAPI endpoints
│   ├── service.py        # invoke / resume graph
│   ├── database.py       # SQLite: customers, orders
│   ├── session_store.py  # SQLite: dialog memory
│   ├── prompts/          # YAML prompt templates
│   └── graph/
│       ├── state.py
│       ├── nodes.py
│       └── builder.py
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   └── ROADMAP.md
├── scripts/
│   └── dev.ps1
├── requirements.txt
└── .env.example
```

## Production next steps

- Postgres вместо SQLite
- Redis для sessions
- PostgresSaver для LangGraph checkpointing
- Langfuse / LangSmith для traces
- WebSocket streaming для chat widget
