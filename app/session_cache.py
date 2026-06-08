"""Hot session cache in Redis (Postgres remains source of truth)."""

from __future__ import annotations

from typing import Any

from app.cache import cache_backend, cache_delete, cache_get, cache_set
from app.config import settings


def _session_key(session_id: str, *, tenant_id: str) -> str:
    return f"session:{tenant_id}:{session_id}"


def session_cache_enabled() -> bool:
    return bool(settings.redis_url) and cache_backend() == "redis"


def get_cached_session(session_id: str, *, tenant_id: str) -> dict | None:
    if not session_cache_enabled():
        return None
    payload = cache_get(_session_key(session_id, tenant_id=tenant_id))
    return payload if isinstance(payload, dict) else None


def set_cached_session(
    session_id: str,
    payload: dict[str, Any],
    *,
    tenant_id: str,
) -> None:
    if not session_cache_enabled():
        return
    cache_set(
        _session_key(session_id, tenant_id=tenant_id),
        payload,
        ttl=settings.session_cache_ttl_seconds,
    )


def invalidate_cached_session(session_id: str, *, tenant_id: str) -> None:
    if not session_cache_enabled():
        return
    cache_delete(_session_key(session_id, tenant_id=tenant_id))
