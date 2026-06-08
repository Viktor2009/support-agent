import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

_buckets: dict[str, list[float]] = defaultdict(list)
_LIMITED_PATHS = {"/chat", "/chat/resume", "/chat/feedback"}


def reset_rate_limit() -> None:
    _buckets.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        limit = settings.rate_limit_per_minute
        if not limit or request.url.path not in _LIMITED_PATHS:
            return await call_next(request)

        client_host = request.client.host if request.client else "unknown"
        now = time.time()
        window = [t for t in _buckets[client_host] if now - t < 60]
        if len(window) >= limit:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        window.append(now)
        _buckets[client_host] = window
        return await call_next(request)
