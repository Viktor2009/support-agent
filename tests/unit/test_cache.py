from app.cache import cache_get, cache_set, reset_cache
from app.cached_db import set_cached_order
from app.database import get_order_status


def test_memory_cache_roundtrip():
    reset_cache()
    cache_set("test:key", {"ok": True}, ttl=60)
    assert cache_get("test:key") == {"ok": True}


def test_order_status_uses_cache(isolated_env, monkeypatch):
    reset_cache()
    set_cached_order(1, "cust_456", {"order_id": 1, "status": "cached"})
    result = get_order_status(1, "cust_456")
    assert result["status"] == "cached"
