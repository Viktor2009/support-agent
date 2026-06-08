from fastapi import Header, HTTPException

from app.config import settings


def require_admin(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin API is not configured")
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
