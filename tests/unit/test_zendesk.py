from app.integrations.zendesk import create_ticket


def test_zendesk_mock_ticket(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "zendesk_subdomain", "")
    monkeypatch.setattr(settings, "zendesk_mock", True)
    monkeypatch.setattr(settings, "mock_llm", True)

    ticket_id = create_ticket(
        session_id="session-abc12345",
        customer_id="cust_456",
        reason="complaint",
        transcript=["test message"],
    )
    assert ticket_id == "MOCK-SESSION-"


def test_zendesk_disabled_without_mock(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "zendesk_subdomain", "")
    monkeypatch.setattr(settings, "zendesk_mock", False)
    monkeypatch.setattr(settings, "mock_llm", False)

    ticket_id = create_ticket(
        session_id="s1",
        customer_id="cust_456",
        reason="test",
        transcript=["hi"],
    )
    assert ticket_id is None
