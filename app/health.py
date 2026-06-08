from sqlalchemy import text

from app import database
from app.async_database import ping_database_async
from app.cache import cache_backend, ping_cache
from app.checkpointer import ping_checkpointer
from app.config import settings
from app.rag.index import index_mode, index_size
from app.rag.retriever import resolve_rag_mode
from app.session_cache import session_cache_enabled


def check_database() -> str:
    try:
        with database.SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


async def build_health_payload() -> dict:
    db_status = check_database()
    db_async = await ping_database_async()
    cp_status = await ping_checkpointer()
    langfuse = (
        "configured"
        if settings.langfuse_public_key and settings.langfuse_secret_key
        else "disabled"
    )
    overall = (
        "ok"
        if db_status == "ok"
        and db_async == "ok"
        and cp_status not in ("error", "not_initialized")
        else "degraded"
    )
    return {
        "status": overall,
        "version": settings.app_version,
        "database": db_status,
        "database_async": db_async,
        "checkpointer": cp_status,
        "cache": ping_cache() if settings.redis_url else cache_backend(),
        "langfuse": langfuse,
        "auth": "enabled" if settings.api_keys.strip() else "disabled",
        "rate_limit": settings.rate_limit_per_minute or "disabled",
        "rag": {
            "mode": resolve_rag_mode(),
            "index": index_mode(),
            "chunks": index_size(),
        },
        "metrics": "enabled" if settings.metrics_enabled else "disabled",
        "session_cache": "redis" if session_cache_enabled() else "disabled",
    }
