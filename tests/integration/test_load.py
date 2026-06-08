from concurrent.futures import ThreadPoolExecutor, as_completed


def _post_chat(client, session_id: str) -> int:
    response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "Где мой заказ #1?",
            "customer_id": "cust_456",
        },
    )
    return response.status_code


def test_concurrent_chat_requests(client):
    """Smoke load: 10 parallel /chat calls in-process."""
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(_post_chat, client, f"load-smoke-{i}") for i in range(10)]
        statuses = [future.result() for future in as_completed(futures)]
    assert statuses.count(200) == 10
