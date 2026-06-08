from sqlalchemy import delete, select

from app import async_database
from app.async_session_store import ainvalidate_session_cache
from app.database import ChatSession, Feedback
from app.tenant import DEFAULT_TENANT


def _session_factory():
    if async_database.AsyncSessionLocal is None:
        async_database.init_async_db()
    return async_database.AsyncSessionLocal


async def aget_session(session_id: str, *, tenant_id: str = DEFAULT_TENANT) -> dict | None:
    session_maker = _session_factory()
    async with session_maker() as session:
        row = (
            await session.execute(
                select(ChatSession).where(
                    ChatSession.session_id == session_id,
                    ChatSession.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return None
        return {
            "session_id": row.session_id,
            "tenant_id": row.tenant_id,
            "customer_id": row.customer_id,
            "summary": row.summary or "",
            "messages": row.messages or [],
            "status": row.status,
            "ticket_id": row.ticket_id,
        }


async def alist_feedback_for_session(
    session_id: str, *, tenant_id: str = DEFAULT_TENANT
) -> list[dict]:
    session_maker = _session_factory()
    async with session_maker() as session:
        rows = (
            await session.execute(
                select(Feedback).where(
                    Feedback.session_id == session_id,
                    Feedback.tenant_id == tenant_id,
                )
            )
        ).scalars().all()
        return [
            {
                "feedback_id": row.feedback_id,
                "session_id": row.session_id,
                "customer_id": row.customer_id,
                "rating": row.rating,
                "comment": row.comment,
            }
            for row in rows
        ]


async def adelete_session(session_id: str, *, tenant_id: str = DEFAULT_TENANT) -> None:
    session_maker = _session_factory()
    async with session_maker() as session:
        await session.execute(
            delete(Feedback).where(
                Feedback.session_id == session_id,
                Feedback.tenant_id == tenant_id,
            )
        )
        await session.execute(
            delete(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.tenant_id == tenant_id,
            )
        )
        await session.commit()
    await ainvalidate_session_cache(session_id, tenant_id=tenant_id)


async def aexport_session_data(
    session_id: str, *, tenant_id: str, customer_id: str
) -> dict:
    session = await aget_session(session_id, tenant_id=tenant_id)
    if session is None:
        raise LookupError("Session not found")
    if session["customer_id"] and session["customer_id"] != customer_id:
        raise PermissionError("Session belongs to another customer")
    feedback = await alist_feedback_for_session(session_id, tenant_id=tenant_id)
    return {
        "session_id": session_id,
        "tenant_id": tenant_id,
        "customer_id": customer_id,
        "session": session,
        "feedback": feedback,
    }


async def adelete_session_data(
    session_id: str, *, tenant_id: str, customer_id: str
) -> None:
    session = await aget_session(session_id, tenant_id=tenant_id)
    if session is None:
        raise LookupError("Session not found")
    if session["customer_id"] and session["customer_id"] != customer_id:
        raise PermissionError("Session belongs to another customer")
    await adelete_session(session_id, tenant_id=tenant_id)
