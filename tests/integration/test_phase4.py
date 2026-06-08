def test_chat_returns_active_agent(client):
    response = client.post(
        "/chat",
        json={
            "session_id": "p4-agent",
            "message": "Где мой заказ #1?",
            "customer_id": "cust_456",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["active_agent"] == "orders_agent"
    assert data["tenant_id"] == "default"


def test_tenant_isolation_with_api_key(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(
        settings,
        "api_keys",
        "default:cust_456:default-key,acme:cust_acme:acme-key",
    )

    default_resp = client.post(
        "/chat",
        headers={"X-API-Key": "default-key"},
        json={"session_id": "p4-default", "message": "Где мой заказ #1?"},
    )
    assert default_resp.status_code == 200
    assert "shipped" in default_resp.json()["answer"].lower()

    acme_resp = client.post(
        "/chat",
        headers={"X-API-Key": "acme-key"},
        json={"session_id": "p4-acme", "message": "Где мой заказ #4?"},
    )
    assert acme_resp.status_code == 200
    acme_data = acme_resp.json()
    assert acme_data["tenant_id"] == "acme"
    assert acme_data["active_agent"] == "orders_agent"
    assert "9900" in acme_data["answer"] or "shipped" in acme_data["answer"].lower()


def test_gdpr_export_and_delete(client):
    session_id = "p4-gdpr"
    chat = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Привет!",
            "customer_id": "cust_456",
        },
    )
    assert chat.status_code == 200

    export = client.get(
        f"/gdpr/sessions/{session_id}/export",
        params={"customer_id": "cust_456"},
    )
    assert export.status_code == 200
    body = export.json()
    assert body["session_id"] == session_id
    assert body["session"]["messages"]

    deleted = client.delete(
        f"/gdpr/sessions/{session_id}",
        params={"customer_id": "cust_456"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"

    missing = client.get(
        f"/gdpr/sessions/{session_id}/export",
        params={"customer_id": "cust_456"},
    )
    assert missing.status_code == 404
