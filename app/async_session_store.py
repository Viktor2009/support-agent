from sqlalchemy import select

from app import async_database
from app.database import ChatSession
from app.tenant import DEFAULT_TENANT


def _session_factory():
    if async_database.AsyncSessionLocal is None:
        async_database.init_async_db()
    return async_database.AsyncSessionLocal


async def aload_session(session_id: str, *, tenant_id: str = DEFAULT_TENANT) -> dict:
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
        return {"customer_id": None, "summary": "", "messages": []}
    return {
        "customer_id": row.customer_id,
        "summary": row.summary or "",
        "messages": row.messages or [],
    }


async def asave_session(
    session_id: str,
    customer_id: str | None,
    summary: str,
    messages: list[dict],
    *,
    tenant_id: str = DEFAULT_TENANT,
    status: str = "active",
    ticket_id: str | None = None,
) -> None:
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
        if row is None:
            row = ChatSession(session_id=session_id, tenant_id=tenant_id)
            session.add(row)
        row.customer_id = customer_id
        row.summary = summary
        row.messages = messages
        row.status = status
        if ticket_id is not None:
            row.ticket_id = ticket_id
        await session.commit()
