def test_health_includes_async_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database_async"] == "ok"
    assert data["version"] == "1.3.0"


def test_security_headers(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Request-ID"]


def test_security_request_id_passthrough(client):
    response = client.get("/health", headers={"X-Request-ID": "trace-abc"})
    assert response.headers["X-Request-ID"] == "trace-abc"
