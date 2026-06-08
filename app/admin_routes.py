from fastapi import APIRouter, Depends, Query

from app import database
from app.admin_auth import require_admin

router = APIRouter(prefix="/admin/api", tags=["admin"])


@router.get("/sessions")
def admin_list_sessions(
    _: None = Depends(require_admin),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    return {"sessions": database.list_sessions(status=status, limit=limit)}


@router.get("/escalations")
def admin_escalations(
    _: None = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
):
    return {"sessions": database.list_sessions(status="awaiting_operator", limit=limit)}


@router.get("/stats")
def admin_stats(_: None = Depends(require_admin)):
    return database.get_analytics_stats()


@router.get("/feedback")
def admin_feedback(
    _: None = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
):
    return {"feedback": database.list_feedback(limit=limit)}
