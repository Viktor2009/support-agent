def test_websocket_chat_done(client):
    with client.websocket_connect("/chat/ws") as ws:
        ws.send_json(
            {
                "session_id": "ws-test-1",
                "message": "Где мой заказ #1?",
                "customer_id": "cust_456",
            }
        )
        saw_done = False
        for _ in range(50):
            msg = ws.receive_json()
            if msg["event"] == "done":
                saw_done = True
                assert msg["data"]["answer"]
                break
            if msg["event"] == "error":
                raise AssertionError(msg["data"])
        assert saw_done
