import httpx

from app.config import settings


def zendesk_configured() -> bool:
    return bool(
        settings.zendesk_subdomain and settings.zendesk_api_token and settings.zendesk_email
    )


def create_ticket(
    *,
    session_id: str,
    customer_id: str | None,
    reason: str,
    transcript: list[str],
) -> str | None:
    if not zendesk_configured():
        if settings.mock_llm or settings.zendesk_mock:
            return f"MOCK-{session_id[:8].upper()}"
        return None

    subject = f"[Support Agent] {reason} — {customer_id or 'unknown'}"
    body = "\n".join(f"- {line}" for line in transcript[-10:])
    payload = {
        "ticket": {
            "subject": subject,
            "comment": {"body": body},
            "tags": ["ai-agent", reason.replace(" ", "_")],
            "requester": {
                "name": customer_id or "Customer",
                "email": f"{customer_id or 'unknown'}@placeholder.local",
            },
        }
    }
    url = f"https://{settings.zendesk_subdomain}.zendesk.com/api/v2/tickets.json"
    try:
        response = httpx.post(
            url,
            json=payload,
            auth=(f"{settings.zendesk_email}/token", settings.zendesk_api_token),
            timeout=10.0,
        )
        response.raise_for_status()
        return str(response.json()["ticket"]["id"])
    except Exception:
        return None
