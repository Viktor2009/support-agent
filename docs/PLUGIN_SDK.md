# Plugin SDK — custom tools

Расширяйте агента без правок ядра: зарегистрируйте async-tool и вызовите его из графа через supervisor / `query_db`.

## Быстрый старт

1. Создайте модуль, например `plugins/my_tools.py`
2. Реализуйте `register(register_tool)`
3. Укажите в `.env`:

```env
PLUGIN_MODULE=plugins.example_promo
```

4. Перезапустите API — tool появится в registry

## Пример (в репозитории)

`plugins/example_promo.py`:

```python
async def lookup_promo(code: str, *, tenant_id: str = "default") -> dict:
    ...

def register(register_tool):
    register_tool("lookup_promo", lookup_promo)
```

Проверка:

```powershell
$env:PLUGIN_MODULE = "plugins.example_promo"
.\scripts\dev.ps1 -Task run
```

```python
from app.tools.registry import arun_tool
await arun_tool("lookup_promo", code="SAVE10", tenant_id="default")
```

## API registry

| Функция | Описание |
|---------|----------|
| `register_tool(name, fn)` | Регистрация tool |
| `arun_tool(name, **kwargs)` | Async вызов (graph nodes) |
| `list_tools()` | Список имён |
| `get_tool(name)` | Получить callable |

## Контракт tool-функции

- Предпочтительно `async def`
- Sync `def` тоже поддерживается (`arun_tool` обернёт)
- Именованные аргументы: как минимум те, что передаёт граф
- Multi-tenant: принимайте `tenant_id: str = "default"`
- Возвращайте `dict` — сериализуемый JSON-like результат

## Встроенные tools

| Name | Описание |
|------|----------|
| `get_order_status` | Статус заказа |
| `list_customer_orders` | Список заказов |
| `list_customer_invoices` | Счета |
| `get_account_info` | Профиль клиента |

## Admin: список tools

```
GET /admin/api/tools
Header: X-Admin-Key
```

## Подключение tool к intent (advanced)

Сейчас mapping intent → tool в `app/graph/nodes.py` (`query_db`).
Для кастомных intent потребуется расширить supervisor и `query_db` routing.

## Docker

`PLUGIN_MODULE` передаётся через environment в `docker-compose.staging.yml`.
Модуль должен быть в образе — скопируйте `plugins/` в Dockerfile (уже включено).

## Тестирование плагина

```powershell
$env:PLUGIN_MODULE = "plugins.example_promo"
$env:MOCK_LLM = "true"
pytest tests/unit/test_plugins.py -v
```
