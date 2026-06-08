from sqlalchemy import func, select

from app import async_database
from app.database import ChatSession, Feedback
from app.tenant import DEFAULT_TENANT


def _session_factory():
    if async_database.AsyncSessionLocal is None:
        async_database.init_async_db()
    return async_database.AsyncSessionLocal


async def alist_sessions(
    status: str | None = None,
    limit: int = 50,
    *,
    tenant_id: str | None = None,
) -> list[dict]:
    session_maker = _session_factory()
    async with session_maker() as session:
        stmt = select(ChatSession)
        if tenant_id:
            stmt = stmt.where(ChatSession.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(ChatSession.status == status)
        stmt = stmt.order_by(ChatSession.updated_at.desc()).limit(limit)
        rows = (await session.execute(stmt)).scalars().all()
        return [
            {
                "session_id": row.session_id,
                "tenant_id": row.tenant_id,
                "customer_id": row.customer_id,
                "status": row.status,
                "summary": row.summary,
                "ticket_id": row.ticket_id,
                "message_count": len(row.messages or []),
            }
            for row in rows
        ]


async def aget_analytics_stats(*, tenant_id: str | None = None) -> dict:
    session_maker = _session_factory()
    async with session_maker() as session:
        session_filters = []
        feedback_filters = []
        if tenant_id:
            session_filters.append(ChatSession.tenant_id == tenant_id)
            feedback_filters.append(Feedback.tenant_id == tenant_id)

        total_stmt = select(func.count()).select_from(ChatSession)
        for clause in session_filters:
            total_stmt = total_stmt.where(clause)
        total_sessions = (await session.execute(total_stmt)).scalar_one()

        awaiting_stmt = select(func.count()).select_from(ChatSession).where(
            ChatSession.status == "awaiting_operator",
            *session_filters,
        )
        awaiting = (await session.execute(awaiting_stmt)).scalar_one()

        closed_stmt = select(func.count()).select_from(ChatSession).where(
            ChatSession.status == "closed",
            *session_filters,
        )
        closed = (await session.execute(closed_stmt)).scalar_one()

        feedback_stmt = select(Feedback)
        for clause in feedback_filters:
            feedback_stmt = feedback_stmt.where(clause)
        feedback_rows = (await session.execute(feedback_stmt)).scalars().all()
        avg_rating = None
        if feedback_rows:
            avg_rating = round(
                sum(row.rating for row in feedback_rows) / len(feedback_rows),
                2,
            )
        return {
            "sessions_total": total_sessions,
            "sessions_awaiting_operator": awaiting,
            "sessions_closed": closed,
            "feedback_count": len(feedback_rows),
            "feedback_avg_rating": avg_rating,
        }


async def alist_feedback(limit: int = 50, *, tenant_id: str | None = None) -> list[dict]:
    session_maker = _session_factory()
    async with session_maker() as session:
        stmt = select(Feedback)
        if tenant_id:
            stmt = stmt.where(Feedback.tenant_id == tenant_id)
        stmt = stmt.order_by(Feedback.created_at.desc()).limit(limit)
        rows = (await session.execute(stmt)).scalars().all()
        return [
            {
                "feedback_id": row.feedback_id,
                "tenant_id": row.tenant_id,
                "session_id": row.session_id,
                "customer_id": row.customer_id,
                "rating": row.rating,
                "comment": row.comment,
            }
            for row in rows
        ]


async def asave_feedback(
    session_id: str,
    rating: int,
    customer_id: str | None = None,
    comment: str | None = None,
    *,
    tenant_id: str = DEFAULT_TENANT,
) -> dict:
    session_maker = _session_factory()
    async with session_maker() as session:
        row = Feedback(
            tenant_id=tenant_id,
            session_id=session_id,
            customer_id=customer_id,
            rating=rating,
            comment=comment,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {
            "feedback_id": row.feedback_id,
            "session_id": row.session_id,
            "rating": row.rating,
        }
