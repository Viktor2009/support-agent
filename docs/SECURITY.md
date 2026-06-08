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

- [x] `pip audit` / Dependabot (CI job `audit` + `.github/dependabot.yml`)
- [ ] Postgres: отдельный user с минимальными правами
- [ ] Redis (если используется): auth + network isolation

## LLM

- [ ] Промпты не содержат сырых credentials
- [ ] Langfuse / logs: не писать полные API keys
- [ ] `MOCK_LLM=false` только в production с валидным ключом

---

## Staging profile (`docker-compose.staging.yml`)

При запуске `docker compose -f docker-compose.staging.yml up` следующие пункты **закрыты**:

| Проверка | Статус | Как |
|----------|--------|-----|
| API_KEYS | ✅ | `cust_456:staging-key-cust456` |
| ADMIN_API_KEY | ✅ | `staging-admin-key` |
| CORS restricted | ✅ | whitelist localhost:3000 |
| Rate limiting | ✅ | `RATE_LIMIT_PER_MINUTE=60` |
| Postgres | ✅ | отдельный контейнер, не SQLite |
| Redis cache | ✅ | `REDIS_URL` в compose |
| Dependabot | ✅ | `.github/dependabot.yml` |
| pip audit | ✅ | CI job `audit` |
| Secrets not in git | ✅ | только `.env.example` / `.env.staging.example` |

Smoke test после деплоя staging:

```powershell
.\scripts\dev.ps1 -Task smoke
# или с явными ключами:
python scripts/smoke_test.py --url http://127.0.0.1:8000 `
  --api-key staging-key-cust456 --admin-key staging-admin-key
```

## Review sign-off

| Проверка | Дата | Ответственный |
|----------|------|---------------|
| Auth enabled | 2026-06-08 | staging compose |
| CORS restricted | 2026-06-08 | staging compose |
| Load test 50 sessions | 2026-06-08 | CI loadtest job |
| Runbook tested | | |
| Staging smoke | | |
