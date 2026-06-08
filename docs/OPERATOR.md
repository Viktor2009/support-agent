# Operator Onboarding — Support Agent

## Доступ

| Ресурс | URL | Auth |
|--------|-----|------|
| Admin UI | `/admin-ui/` | Header `X-Admin-Key` |
| Admin API | `/admin/api/*` | Header `X-Admin-Key` |
| Resume HITL | `POST /chat/resume` | `X-API-Key` (если включён) |

## Эскалации (HITL)

1. Клиент отправляет жалобу → ответ `status: awaiting_operator`
2. В Admin UI: **Escalations** — список сессий `awaiting_operator`
3. Оператор отвечает через API:

```powershell
curl -X POST http://HOST/chat/resume `
  -H "Content-Type: application/json" `
  -H "X-API-Key: YOUR_KEY" `
  -d '{"session_id":"s4","operator_reply":"Разберём возврат в течение 24ч","ticket_id":"ZD-001"}'
```

4. Сессия переходит в `closed`, клиент получает ответ оператора

## Zendesk

При эскалации создаётся тикет (`ZENDESK_MOCK=true` локально → `MOCK-{session_id}`).

Поля в interrupt payload: `reason`, `transcript`, `ticket_id`, `customer_id`.

## Мониторинг

- `/health` — database, async DB, checkpointer, cache
- `/admin/api/stats` — сессии, feedback avg
- Langfuse traces (если `LANGFUSE_*` заданы)

## Типичные сценарии

| Ситуация | Действие |
|----------|----------|
| Клиент ждёт оператора | Resume через `/chat/resume` |
| Неверный customer | Проверить `X-API-Key` / tenant |
| Пустой ответ | Проверить `MOCK_LLM` / OpenAI key |
| GDPR запрос | `/gdpr/sessions/{id}/export` или DELETE |
