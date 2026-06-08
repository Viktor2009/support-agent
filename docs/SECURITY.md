# Security Checklist — Production v1.0

## Auth & access

- [ ] `API_KEYS` задан — все `/chat`, `/demo`, `/gdpr` требуют `X-API-Key`
- [ ] `ADMIN_API_KEY` задан — admin API/UI закрыты
- [ ] `CORS_ORIGINS` — не `*` в production (whitelist доменов виджета)
- [ ] Multi-tenant keys: `tenant:customer:key` — изоляция данных по tenant

## Transport & headers

- [x] Security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, …)
- [x] `X-Request-ID` для трассировки
- [ ] TLS termination на reverse proxy (nginx / ALB)
- [ ] Rate limiting: `RATE_LIMIT_PER_MINUTE` > 0

## Data

- [x] Customer data scoped by `tenant_id` + `customer_id`
- [x] GDPR export/delete endpoints с проверкой владельца сессии
- [x] PII masking в GDPR export
- [ ] Secrets только в env / secret manager (не в git)

## Dependencies

- [ ] `pip audit` / Dependabot
- [ ] Postgres: отдельный user с минимальными правами
- [ ] Redis (если используется): auth + network isolation

## LLM

- [ ] Промпты не содержат сырых credentials
- [ ] Langfuse / logs: не писать полные API keys
- [ ] `MOCK_LLM=false` только в production с валидным ключом

## Review sign-off

| Проверка | Дата | Ответственный |
|----------|------|---------------|
| Auth enabled | | |
| CORS restricted | | |
| Load test 50 sessions | | |
| Runbook tested | | |
