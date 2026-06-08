def test_feedback_endpoint(client):
    response = client.post(
        "/chat/feedback",
        json={"session_id": "fb-1", "rating": 5, "customer_id": "cust_456", "comment": "ok"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5
    assert data["feedback_id"]


def test_admin_stats_requires_key(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_api_key", "secret-admin")
    response = client.get("/admin/api/stats")
    assert response.status_code == 403


def test_admin_stats_with_key(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_api_key", "secret-admin")
    response = client.get("/admin/api/stats", headers={"X-Admin-Key": "secret-admin"})
    assert response.status_code == 200
    assert "sessions_total" in response.json()


def test_admin_panel_page(client):
    response = client.get("/admin-ui/")
    assert response.status_code == 200
    assert "Support Admin" in response.text
