import json
import time
from typing import Any

from app.config import settings

_memory: dict[str, tuple[float, str]] = {}
_redis_client = None


def init_cache() -> None:
    global _redis_client
    if not settings.redis_url:
        return
    try:
        import redis

        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
    except Exception:
        _redis_client = None


def shutdown_cache() -> None:
    global _redis_client
    if _redis_client is not None:
        _redis_client.close()
    _redis_client = None
    _memory.clear()


def reset_cache() -> None:
    _memory.clear()


def cache_backend() -> str:
    if _redis_client is not None:
        return "redis"
    return "memory"


def ping_cache() -> str:
    if not settings.redis_url:
        return "disabled"
    if _redis_client is None:
        return "error"
    try:
        _redis_client.ping()
        return "ok"
    except Exception:
        return "error"


def cache_get(key: str) -> Any | None:
    if _redis_client is not None:
        raw = _redis_client.get(key)
        return json.loads(raw) if raw else None

    entry = _memory.get(key)
    if not entry:
        return None
    expires_at, raw = entry
    if expires_at <= time.time():
        del _memory[key]
        return None
    return json.loads(raw)


def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    ttl = ttl or settings.cache_ttl_seconds
    raw = json.dumps(value, ensure_ascii=False)
    if _redis_client is not None:
        _redis_client.setex(key, ttl, raw)
        return
    _memory[key] = (time.time() + ttl, raw)


def cache_delete(key: str) -> None:
    if _redis_client is not None:
        _redis_client.delete(key)
        return
    _memory.pop(key, None)


def cache_delete_prefix(prefix: str) -> None:
    if _redis_client is not None:
        for key in _redis_client.scan_iter(f"{prefix}*"):
            _redis_client.delete(key)
        return
    for key in list(_memory):
        if key.startswith(prefix):
            del _memory[key]
