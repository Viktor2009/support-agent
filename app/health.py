from sqlalchemy import text

from app import database
from app.checkpointer import ping_checkpointer
from app.config import settings


def check_database() -> str:
    try:
        with database.SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


def build_health_payload() -> dict:
    db_status = check_database()
    cp_status = ping_checkpointer()
    langfuse = (
        "configured"
        if settings.langfuse_public_key and settings.langfuse_secret_key
        else "disabled"
    )
    overall = (
        "ok"
        if db_status == "ok" and cp_status not in ("error", "not_initialized")
        else "degraded"
    )
    return {
        "status": overall,
        "version": settings.app_version,
        "database": db_status,
        "checkpointer": cp_status,
        "langfuse": langfuse,
        "auth": "enabled" if settings.api_keys.strip() else "disabled",
    }
