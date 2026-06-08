import time
from collections.abc import Callable

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_registry = CollectorRegistry()

CHAT_REQUESTS = Counter(
    "support_chat_requests_total",
    "Total chat-related HTTP requests",
    ["endpoint", "status"],
    registry=_registry,
)
CHAT_ESCALATIONS = Counter(
    "support_chat_escalations_total",
    "Chat sessions escalated to human operator",
    registry=_registry,
)
CHAT_DURATION = Histogram(
    "support_chat_duration_seconds",
    "Chat endpoint latency in seconds",
    ["endpoint"],
    registry=_registry,
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

_METRICS_PATHS = {"/chat", "/chat/stream", "/chat/resume", "/chat/feedback"}


def reset_metrics() -> None:
    """Clear metrics between tests."""
    global _registry, CHAT_REQUESTS, CHAT_ESCALATIONS, CHAT_DURATION
    _registry = CollectorRegistry()
    CHAT_REQUESTS = Counter(
        "support_chat_requests_total",
        "Total chat-related HTTP requests",
        ["endpoint", "status"],
        registry=_registry,
    )
    CHAT_ESCALATIONS = Counter(
        "support_chat_escalations_total",
        "Chat sessions escalated to human operator",
        registry=_registry,
    )
    CHAT_DURATION = Histogram(
        "support_chat_duration_seconds",
        "Chat endpoint latency in seconds",
        ["endpoint"],
        registry=_registry,
        buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )


def record_chat_request(endpoint: str, status_code: int, duration_seconds: float) -> None:
    status = str(status_code)
    CHAT_REQUESTS.labels(endpoint=endpoint, status=status).inc()
    CHAT_DURATION.labels(endpoint=endpoint).observe(duration_seconds)


def record_escalation() -> None:
    CHAT_ESCALATIONS.inc()


def metrics_payload() -> bytes:
    return generate_latest(_registry)


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        if path not in _METRICS_PATHS:
            return await call_next(request)

        started = time.perf_counter()
        response = await call_next(request)
        record_chat_request(path, response.status_code, time.perf_counter() - started)
        return response
