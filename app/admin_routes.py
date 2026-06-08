from fastapi import APIRouter, Depends, Query

from app import database
from app.admin_auth import require_admin
from app.executor import run_sync

router = APIRouter(prefix="/admin/api", tags=["admin"])


@router.get("/sessions")
async def admin_list_sessions(
    _: None = Depends(require_admin),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    sessions = await run_sync(database.list_sessions, status=status, limit=limit)
    return {"sessions": sessions}


@router.get("/escalations")
async def admin_escalations(
    _: None = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
):
    sessions = await run_sync(
        database.list_sessions,
        status="awaiting_operator",
        limit=limit,
    )
    return {"sessions": sessions}


@router.get("/stats")
async def admin_stats(_: None = Depends(require_admin)):
    return await run_sync(database.get_analytics_stats)


@router.get("/feedback")
async def admin_feedback(
    _: None = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
):
    feedback = await run_sync(database.list_feedback, limit=limit)
    return {"feedback": feedback}
