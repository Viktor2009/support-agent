import asyncio

from app.async_session_store import aload_session, asave_session
from app.session_cache import (
    get_cached_session,
    invalidate_cached_session,
    set_cached_session,
)


def test_session_cache_roundtrip(monkeypatch):
    store: dict = {}

    monkeypatch.setattr(
        "app.session_cache.session_cache_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.session_cache.cache_get",
        lambda key: store.get(key),
    )
    monkeypatch.setattr(
        "app.session_cache.cache_set",
        lambda key, value, ttl=None: store.__setitem__(key, value),
    )
    monkeypatch.setattr(
        "app.session_cache.cache_delete",
        lambda key: store.pop(key, None),
    )

    set_cached_session(
        "cache-1",
        {"customer_id": "cust_456", "summary": "hi", "messages": []},
        tenant_id="default",
    )
    cached = get_cached_session("cache-1", tenant_id="default")
    assert cached["summary"] == "hi"
    invalidate_cached_session("cache-1", tenant_id="default")
    assert get_cached_session("cache-1", tenant_id="default") is None


def test_aload_session_reads_cache(monkeypatch, isolated_env):
    monkeypatch.setattr(
        "app.async_session_store.get_cached_session",
        lambda session_id, tenant_id="default": {
            "customer_id": "cust_456",
            "summary": "from-cache",
            "messages": [{"role": "user", "content": "test"}],
        },
    )
    result = asyncio.run(aload_session("cached-session"))
    assert result["summary"] == "from-cache"


def test_asave_session_populates_cache(monkeypatch, isolated_env):
    captured: dict = {}

    def fake_set(session_id, payload, *, tenant_id="default"):
        captured["payload"] = payload

    monkeypatch.setattr("app.async_session_store.set_cached_session", fake_set)
    asyncio.run(
        asave_session(
            "save-1",
            "cust_456",
            "summary",
            [{"role": "user", "content": "hello"}],
        )
    )
    assert captured["payload"]["summary"] == "summary"
