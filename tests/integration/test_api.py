def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_order_status(client):
    response = client.post(
        "/chat",
        json={
            "session_id": "api-1",
            "message": "Где мой заказ #1?",
            "customer_id": "cust_456",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "order_status"
    assert data["answer"]


def test_demo_order_not_found(client):
    response = client.get("/demo/orders/9999")
    assert response.status_code == 404


def test_demo_customer(client):
    response = client.get("/demo/customers/cust_456")
    assert response.status_code == 200
    body = response.json()
    assert body["customer"]["plan"] == "pro"
    assert len(body["orders"]) >= 1
