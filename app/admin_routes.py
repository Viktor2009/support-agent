from fastapi import APIRouter, Depends, Query

from app.admin_auth import require_admin
from app.async_admin import (
    aget_analytics_stats,
    alist_feedback,
    alist_sessions,
)
from app.tools.registry import list_tools

router = APIRouter(prefix="/admin/api", tags=["admin"])


@router.get("/sessions")
async def admin_list_sessions(
    _: None = Depends(require_admin),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    sessions = await alist_sessions(status=status, limit=limit)
    return {"sessions": sessions}


@router.get("/escalations")
async def admin_escalations(
    _: None = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
):
    sessions = await alist_sessions(status="awaiting_operator", limit=limit)
    return {"sessions": sessions}


@router.get("/stats")
async def admin_stats(_: None = Depends(require_admin)):
    return await aget_analytics_stats()


@router.get("/feedback")
async def admin_feedback(
    _: None = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
):
    feedback = await alist_feedback(limit=limit)
    return {"feedback": feedback}


@router.get("/tools")
async def admin_tools(_: None = Depends(require_admin)):
    return {"tools": list_tools()}
