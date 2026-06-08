# Руководство по проверке и тестированию

Пошаговый план: что уже настроено, что запускать, **ваши действия**.

---

## Текущее состояние (проверено)

| Компонент | Статус |
|-----------|--------|
| Docker staging (app + postgres + redis) | Запущен на `:8000` |
| Smoke test | 5/5 OK |
| GitHub CI | test + audit + loadtest + staging + A/B eval |
| Версия API | 1.7.0 |

---

## Быстрая проверка (одна команда)

```powershell
cd c:\AI_pom\support-agent
.\scripts\verify.ps1
```

Пропустить Docker / unit-тесты (только smoke):

```powershell
.\scripts\verify.ps1 -SkipTests
.\scripts\verify.ps1 -SkipDocker -SkipTests   # только smoke
```

---

## Режимы тестирования

### A. Staging в Docker (рекомендуется)

Полный стек: Postgres, Redis, API keys, session cache.

```powershell
cd c:\AI_pom\support-agent

# Запуск (если не запущен)
.\scripts\dev.ps1 -Task staging

# Проверка
.\scripts\dev.ps1 -Task smoke
```

| URL | Назначение |
|-----|------------|
| http://127.0.0.1:8000/docs | Swagger API |
| http://127.0.0.1:8000/health | Статус системы |
| http://127.0.0.1:8000/widget/?customer_id=cust_456&api_key=staging-key-cust456 | Чат-виджет |
| http://127.0.0.1:8000/widget/?customer_id=cust_456&api_key=staging-key-cust456&transport=ws | WebSocket |
| http://127.0.0.1:8000/admin-ui/ | Admin (ключ ниже) |
| http://127.0.0.1:8000/metrics | Prometheus |

**Ключи staging:**

| Заголовок | Значение |
|-----------|----------|
| `X-API-Key` | `staging-key-cust456` |
| `X-Admin-Key` | `staging-admin-key` |

### B. Локально без Docker (разработка)

```powershell
.\.venv\Scripts\Activate.ps1
$env:MOCK_LLM = "true"
.\scripts\dev.ps1 -Task run
```

В другом терминале: `.\scripts\dev.ps1 -Task smoke` (без api-key).

### C. Автотесты (как в CI)

```powershell
$env:MOCK_LLM = "true"
.\scripts\dev.ps1 -Task lint
.\scripts\dev.ps1 -Task test
.\scripts\dev.ps1 -Task eval
.\scripts\dev.ps1 -Task ab-eval
.\scripts\dev.ps1 -Task loadtest   # нужен запущенный API на :8000
```

---

## Сценарии ручного теста (чеклист)

Отметьте после проверки в браузере / curl:

- [ ] **Заказ:** «Где мой заказ #1?» → ответ со статусом `shipped`
- [ ] **Список:** «Покажи все мои заказы» → список
- [ ] **FAQ:** «Сколько дней на возврат?» → из knowledge base
- [ ] **Эскалация:** «Хочу возврат, сервис ужасный!» → `awaiting_operator`
- [ ] **Виджет SSE** — стриминг ответа по буквам
- [ ] **Виджет WS** — `?transport=ws`
- [ ] **Admin** — статистика сессий открывается с admin key
- [ ] **Feedback** — POST `/chat/feedback` rating 5

Пример curl (staging):

```powershell
curl -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -H "X-API-Key: staging-key-cust456" `
  -d '{"session_id":"manual-1","message":"Где мой заказ #1?"}'
```

---

## Ваши действия (по приоритету)

### Сейчас (30 мин) — базовая проверка

1. Убедитесь, что Docker Desktop запущен.
2. Выполните `.\scripts\verify.ps1`.
3. Откройте виджет в браузере (URL выше).
4. Пройдите чеклист сценариев вручную.

### На этой неделе — тест с реальным LLM

1. Получите ключ OpenAI: https://platform.openai.com/api-keys
2. Создайте `.env.local` или отредактируйте `.env`:

```env
MOCK_LLM=false
OPENAI_API_KEY=sk-ваш-реальный-ключ
```

3. Для Docker staging добавьте в `docker-compose.staging.yml` (секция `app.environment`):

```yaml
MOCK_LLM: "false"
OPENAI_API_KEY: sk-ваш-ключ   # лучше через .env file, не коммитить!
```

4. Перезапуск: `docker compose -f docker-compose.staging.yml up --build -d`
5. Повторите smoke + ручные сценарии — ответы будут от GPT, не mock.

6. Eval с real LLM:

```powershell
$env:OPENAI_API_KEY = "sk-..."
.\scripts\dev.ps1 -Task eval-real
.\scripts\dev.ps1 -Task ab-eval
```

### Опционально — Langfuse (мониторинг + A/B dashboard)

1. Регистрация: https://cloud.langfuse.com
2. Создайте проект → скопируйте Public/Secret keys
3. В environment Docker / `.env`:

```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

4. `.\scripts\dev.ps1 -Task ab-eval-langfuse`
5. В UI Langfuse: Scores → filter `intent_correct`, metadata `variant`

Подробнее: [LANGFUSE.md](LANGFUSE.md)

### Опционально — Plugin tool

```powershell
$env:PLUGIN_MODULE = "plugins.example_promo"
.\scripts\dev.ps1 -Task run
```

Документация: [PLUGIN_SDK.md](PLUGIN_SDK.md)

### Pilot с пользователями (2+ недели)

Следуйте [PILOT.md](PILOT.md):

1. TLS + домен ([TLS.md](TLS.md))
2. Закрыть [SECURITY.md](SECURITY.md)
3. 10–50 тестовых пользователей на виджет
4. Мониторинг `/metrics` + admin feedback

---

## Что НЕ нужно делать

- Не коммитьте `.env` с реальными ключами в git
- Не включайте `MOCK_LLM=true` в production pilot
- Не открывайте admin без `ADMIN_API_KEY`

---

## Если что-то сломалось

| Проблема | Решение |
|----------|---------|
| Docker не стартует | Запустить Docker Desktop, подождать 1–2 мин |
| Порт 8000 занят | `netstat -ano \| findstr :8000` или сменить порт в compose |
| Smoke 401 | Добавить `--api-key staging-key-cust456` |
| app container Exited | `docker logs support-agent-app-1` |
| Тесты падают локально | `$env:MOCK_LLM="true"` перед pytest |

Runbook: [RUNBOOK.md](RUNBOOK.md)

---

## Ссылки

| Документ | Содержание |
|----------|------------|
| [PILOT.md](PILOT.md) | Pilot с реальными пользователями |
| [OPERATOR.md](OPERATOR.md) | Работа оператора |
| [SECURITY.md](SECURITY.md) | Security checklist |
| [RUNBOOK.md](RUNBOOK.md) | Деплой, откат, инциденты |
