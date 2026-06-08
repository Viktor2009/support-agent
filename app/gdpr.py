from app import database
from app.privacy import mask_pii_text


def export_session_data(session_id: str, *, tenant_id: str, customer_id: str) -> dict:
    session = database.get_session(session_id, tenant_id=tenant_id)
    if session is None:
        raise LookupError("Session not found")
    if session["customer_id"] and session["customer_id"] != customer_id:
        raise PermissionError("Session belongs to another customer")

    feedback = database.list_feedback_for_session(session_id, tenant_id=tenant_id)
    return {
        "session_id": session_id,
        "tenant_id": tenant_id,
        "customer_id": customer_id,
        "session": session,
        "feedback": feedback,
    }


def delete_session_data(session_id: str, *, tenant_id: str, customer_id: str) -> None:
    session = database.get_session(session_id, tenant_id=tenant_id)
    if session is None:
        raise LookupError("Session not found")
    if session["customer_id"] and session["customer_id"] != customer_id:
        raise PermissionError("Session belongs to another customer")
    database.delete_session(session_id, tenant_id=tenant_id)


def redact_transcript(messages: list[dict]) -> list[dict]:
    return [
        {
            **message,
            "content": mask_pii_text(message.get("content", "")),
        }
        for message in messages
    ]
