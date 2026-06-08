# Langfuse — tracing и A/B eval dashboards

## Включение tracing (production / staging)

```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

`/health` → `"langfuse": "configured"`.

Каждый `/chat` создаёт trace через LangChain callback (`app/observability.py`).

## A/B eval (intent prompts)

Два промпта классификации:

| Variant | Prompt key | Файл |
|---------|------------|------|
| `a` | `classify_intent` | `app/prompts/intent.yaml` |
| `b` | `classify_intent_b` | тот же файл |

### Локальный запуск

```powershell
# Mock LLM (CI-friendly)
python tests/eval/run_ab_eval.py --no-langfuse

# С выгрузкой scores в Langfuse
python tests/eval/run_ab_eval.py

# Real OpenAI
python tests/eval/run_ab_eval.py --real-llm
```

Или:

```powershell
.\scripts\dev.ps1 -Task ab-eval
.\scripts\dev.ps1 -Task ab-eval-langfuse
```

### Что попадает в Langfuse

На каждый кейс golden dataset:

- Trace `intent-eval` с `input` / `output`
- Score `intent_correct` (1.0 / 0.0)
- Metadata: `variant`, `run_id`, `prompt`

### Dashboard в Langfuse UI

1. Откройте [cloud.langfuse.com](https://cloud.langfuse.com) → **Scores**
2. Фильтр: `name = intent_correct`
3. Group / filter по metadata `variant` → сравнение **a** vs **b**
4. Traces → filter `name = intent-eval`, metadata `run_id`

Рекомендуемый порог: `intent_correct` ≥ 0.85 по каждому variant.

## Production monitoring

- **Traces** — latency, errors, LLM tokens
- **Scores** — подключите feedback (`POST /chat/feedback`) как custom score (future)
- **Sessions** — `session_id` из chat передаётся в Langfuse handler

См. [RUNBOOK.md](RUNBOOK.md) при недоступности LLM.
