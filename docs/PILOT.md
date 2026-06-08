# Pilot — запуск с реальными пользователями

Чеклист для первого pilot на staging/production-like окружении.

## 1. Подготовка (T-7 … T-1)

- [ ] Staging поднят: `docker compose -f docker-compose.staging.yml up`
- [ ] Smoke 5/5: `.\scripts\dev.ps1 -Task smoke`
- [ ] CI green (test + audit + loadtest + staging)
- [ ] `MOCK_LLM=false`, валидный `OPENAI_API_KEY`
- [ ] `API_KEYS`, `ADMIN_API_KEY`, `CORS_ORIGINS` — см. [SECURITY.md](SECURITY.md)
- [ ] TLS через nginx — см. [TLS.md](TLS.md)
- [ ] Langfuse keys (опционально) — см. [LANGFUSE.md](LANGFUSE.md)
- [ ] A/B eval baseline: `python tests/eval/run_ab_eval.py --no-langfuse`

## 2. Когорта pilot

| Параметр | Рекомендация |
|----------|--------------|
| Размер | 10–50 активных пользователей |
| Длительность | 2 недели |
| Канал | Chat widget на тестовой странице |
| Поддержка | 1 оператор on-call (см. [OPERATOR.md](OPERATOR.md)) |

Демо-данные: `cust_456`, заказы #1–#2. Для изоляции — tenant `acme` / `cust_acme`.

## 3. День запуска (T-0)

```powershell
# Production-like
docker compose -f docker-compose.staging.yml up -d
.\scripts\dev.ps1 -Task smoke

# Мониторинг
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics
```

Виджет:

```
https://your-domain/widget/?customer_id=cust_456&api_key=YOUR_KEY
```

## 4. Метрики pilot

| Метрика | Цель (roadmap) | Где смотреть |
|---------|----------------|--------------|
| % без эскалации | ≥ 40% | Admin stats, Langfuse |
| p95 latency | < 5 с | Prometheus histogram |
| Intent accuracy | ≥ 85% | `run_eval.py`, Langfuse scores |
| Grounding | ≥ 90% | Manual review sample |

```promql
# Пример: доля эскалаций
rate(support_chat_escalations_total[5m])
/ rate(support_chat_requests_total[5m])
```

## 5. Feedback loop

- Пользователи: кнопка оценки → `POST /chat/feedback`
- Операторы: `/admin-ui/` → escalations, feedback
- Еженедельно: `run_ab_eval` + разбор failures в golden dataset

## 6. Критерии успеха / rollback

**Успех pilot** → переход в GA:

- 2 недели без P1 инцидентов
- Метрики в целевых порогах
- Security checklist закрыт

**Rollback** (см. [RUNBOOK.md](RUNBOOK.md)):

1. `MOCK_LLM=true` — emergency only
2. Откат Docker image / git tag
3. Уведомить операторов — ручная обработка эскалаций
4. Post-mortem: обновить golden dataset + prompts

## 7. После pilot

- [ ] Расширить `knowledge/*.md` по частым вопросам
- [ ] Добавить кейсы в `golden_dataset.jsonl`
- [ ] Plugin tools для интеграций (CRM, billing) — [PLUGIN_SDK.md](PLUGIN_SDK.md)
- [ ] Масштабирование: Redis sessions, Postgres replicas
