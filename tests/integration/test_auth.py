def test_chat_requires_api_key_when_auth_enabled(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "api_keys", "cust_456:test-secret-key")
    response = client.post(
        "/chat",
        json={"session_id": "auth-1", "message": "Где мой заказ #1?"},
    )
    assert response.status_code == 401


def test_chat_with_valid_api_key(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "api_keys", "cust_456:test-secret-key")
    response = client.post(
        "/chat",
        headers={"X-API-Key": "test-secret-key"},
        json={"session_id": "auth-2", "message": "Где мой заказ #1?"},
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "order_status"


def test_chat_rejects_customer_id_mismatch(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "api_keys", "cust_456:test-secret-key")
    response = client.post(
        "/chat",
        headers={"X-API-Key": "test-secret-key"},
        json={
            "session_id": "auth-3",
            "message": "Где мой заказ #1?",
            "customer_id": "cust_789",
        },
    )
    assert response.status_code == 403


def test_health_shows_auth_enabled(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "api_keys", "cust_456:test-secret-key")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["auth"] == "enabled"
