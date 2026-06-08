# Runbook — Support Agent

## Деплой

### Staging (Docker)

```powershell
cd c:\AI_pom\support-agent
.\scripts\dev.ps1 -Task staging
```

Проверка:

```powershell
curl http://127.0.0.1:8000/health
```

Ожидаемо: `"status": "ok"`, `"database": "ok"`.

### Production checklist

1. `DATABASE_URL` → PostgreSQL
2. `API_KEYS` задан (auth включён)
3. `ADMIN_API_KEY` задан
4. `MOCK_LLM=false`, `OPENAI_API_KEY` валиден
5. `alembic upgrade head`
6. `RATE_LIMIT_PER_MINUTE` > 0
7. Опционально: `REDIS_URL`, Langfuse keys

## Откат

1. Остановить контейнер / процесс uvicorn
2. Вернуть предыдущий Docker image или git tag
3. При миграции БД: `alembic downgrade -1` (если нужно)
4. Проверить `/health` и smoke-тест `/chat`

## LLM недоступен

**Симптомы:** timeout, 5xx от OpenAI, пустые ответы.

**Действия:**

1. Включить деградацию: `MOCK_LLM=true` (только для emergency / staging)
2. Проверить `OPENAI_API_KEY` и квоту
3. Уведомить операторов — эскалации (`/admin/api/escalations`) обрабатываются вручную
4. Мониторинг Langfuse traces (если включён)

## Postgres недоступен

**Симптомы:** `/health` → `"database": "error"`, 5xx на `/chat`.

**Действия:**

1. `docker compose ps` / проверить RDS
2. Перезапуск Postgres: `docker compose restart postgres`
3. Проверить `DATABASE_URL`, connection pool
4. Checkpointer на Postgres — без БД HITL resume не работает

## Rate limit (429)

Клиент превысил `RATE_LIMIT_PER_MINUTE`. Увеличить лимит или добавить API gateway throttling per tenant.

## GDPR запрос

```powershell
# Экспорт
curl "http://HOST/gdpr/sessions/SESSION_ID/export?customer_id=CUST_ID" -H "X-API-Key: KEY"

# Удаление
curl -X DELETE "http://HOST/gdpr/sessions/SESSION_ID?customer_id=CUST_ID" -H "X-API-Key: KEY"
```

## Load test

```powershell
# Сервер должен быть запущен с MOCK_LLM=true для стабильного прогона
.\scripts\dev.ps1 -Task run
.\scripts\dev.ps1 -Task loadtest
```

Цель Production v1.0: 50 concurrent sessions без ошибок.

## Smoke после деплоя

```powershell
.\scripts\dev.ps1 -Task test
curl -X POST http://HOST/chat -H "Content-Type: application/json" -d "{\"session_id\":\"smoke-1\",\"message\":\"Где мой заказ #1?\",\"customer_id\":\"cust_456\"}"
```
