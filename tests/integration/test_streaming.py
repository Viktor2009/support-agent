import json


def _parse_sse_events(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in body.strip().split("\n\n"):
        if not block.strip():
            continue
        event = "message"
        data = ""
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        if data:
            events.append((event, json.loads(data)))
    return events


def test_chat_stream_returns_sse(client):
    response = client.post(
        "/chat/stream",
        json={
            "session_id": "stream-1",
            "message": "Где мой заказ #1?",
            "customer_id": "cust_456",
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse_events(response.text)
    event_types = [name for name, _ in events]
    assert "node" in event_types
    assert "token" in event_types
    assert "done" in event_types

    done = next(payload for name, payload in events if name == "done")
    assert done["intent"] == "order_status"
    assert done["active_agent"] == "orders_agent"
    assert done["answer"]

    tokens = "".join(payload["text"] for name, payload in events if name == "token")
    assert tokens == done["answer"]


def test_chat_stream_emits_live_tokens(client):
    """Stream path emits token events (custom stream from synthesize_answer)."""
    response = client.post(
        "/chat/stream",
        json={
            "session_id": "stream-live",
            "message": "Где мой заказ #1?",
            "customer_id": "cust_456",
        },
    )
    events = _parse_sse_events(response.text)
    assert any(
        name == "node" and payload.get("node") == "synthesize_answer"
        for name, payload in events
    )
    assert any(name == "token" for name, _ in events)


def test_chat_stream_escalation_interrupt(client):
    response = client.post(
        "/chat/stream",
        json={
            "session_id": "stream-esc",
            "message": "Хочу возврат, сервис ужасный!",
            "customer_id": "cust_456",
        },
    )
    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert any(name == "interrupt" for name, _ in events)
    interrupt = next(payload for name, payload in events if name == "interrupt")
    assert interrupt["status"] == "awaiting_operator"
