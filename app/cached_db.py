import hashlib

from app.cache import cache_get, cache_set
from app.config import settings


def _order_cache_key(order_id: int, customer_id: str | None) -> str:
    return f"db:order:{order_id}:{customer_id or 'any'}"


def _orders_list_key(customer_id: str) -> str:
    return f"db:orders:{customer_id}"


def _intent_cache_key(message: str, summary: str) -> str:
    digest = hashlib.sha256(f"{message}|{summary}".encode()).hexdigest()[:16]
    return f"intent:{digest}"


def get_cached_order(order_id: int, customer_id: str | None):
    return cache_get(_order_cache_key(order_id, customer_id))


def set_cached_order(order_id: int, customer_id: str | None, data: dict | None) -> None:
    if data is not None:
        cache_set(_order_cache_key(order_id, customer_id), data)


def get_cached_orders_list(customer_id: str):
    return cache_get(_orders_list_key(customer_id))


def set_cached_orders_list(customer_id: str, data: list) -> None:
    cache_set(_orders_list_key(customer_id), data)


def get_cached_intent(message: str, summary: str):
    return cache_get(_intent_cache_key(message, summary))


def set_cached_intent(message: str, summary: str, result: dict) -> None:
    cache_set(_intent_cache_key(message, summary), result, ttl=settings.intent_cache_ttl_seconds)
