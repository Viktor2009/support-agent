def test_metrics_endpoint_returns_prometheus(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert "support_chat_requests_total" in body
    assert "support_chat_duration_seconds" in body


def test_metrics_records_chat_request(client):
    client.post(
        "/chat",
        json={
            "session_id": "metrics-1",
            "message": "Привет!",
            "customer_id": "cust_456",
        },
    )
    response = client.get("/metrics")
    assert response.status_code == 200
    assert 'support_chat_requests_total{endpoint="/chat",status="200"}' in response.text


def test_metrics_disabled_returns_404(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "metrics_enabled", False)
    response = client.get("/metrics")
    assert response.status_code == 404
