from app import database
from app.database import ChatSession


def load_session(session_id: str) -> dict:
    with database.SessionLocal() as db:
        row = db.get(ChatSession, session_id)
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
    status: str = "active",
    ticket_id: str | None = None,
) -> None:
    with database.SessionLocal() as db:
        row = db.get(ChatSession, session_id)
        if row is None:
            row = ChatSession(session_id=session_id)
            db.add(row)
        row.customer_id = customer_id
        row.summary = summary
        row.messages = messages
        row.status = status
        if ticket_id is not None:
            row.ticket_id = ticket_id
        db.commit()
