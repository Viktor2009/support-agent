from app import database
from app.database import ChatSession
from app.tenant import DEFAULT_TENANT


def load_session(session_id: str, *, tenant_id: str = DEFAULT_TENANT) -> dict:
    with database.SessionLocal() as db:
        row = (
            db.query(ChatSession)
            .filter(
                ChatSession.session_id == session_id,
                ChatSession.tenant_id == tenant_id,
            )
            .first()
        )
    if not row:
        return {"customer_id": None, "summary": "", "messages": []}
    return {
        "customer_id": row.customer_id,
        "summary": row.summary or "",
        "messages": row.messages or [],
    }


def save_session(
    session_id: str,
    customer_id: str | None,
    summary: str,
    messages: list[dict],
    *,
    tenant_id: str = DEFAULT_TENANT,
    status: str = "active",
    ticket_id: str | None = None,
) -> None:
    with database.SessionLocal() as db:
        row = (
            db.query(ChatSession)
            .filter(
                ChatSession.session_id == session_id,
                ChatSession.tenant_id == tenant_id,
            )
            .first()
        )
        if row is None:
            row = ChatSession(session_id=session_id, tenant_id=tenant_id)
            db.add(row)
        row.customer_id = customer_id
        row.summary = summary
        row.messages = messages
        row.status = status
        if ticket_id is not None:
            row.ticket_id = ticket_id
        db.commit()
