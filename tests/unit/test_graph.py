from app.service import reset_graph, resume_chat, run_chat


def test_run_chat_order_status():
    result = run_chat("g1", "Где мой заказ #1?", "cust_456")
    assert result.intent == "order_status"
    assert "shipped" in result.answer.lower() or "shipped" in result.answer
    assert result.confidence == "high"


def test_run_chat_dialog_context():
    run_chat("g2", "Привет, вопрос по заказу #1", "cust_456")
    result = run_chat("g2", "Когда доставка?", "cust_456")
    assert result.intent == "order_status"
    assert "2025-06-10" in result.answer or "shipped" in result.answer.lower()


def test_run_chat_account_info():
    result = run_chat("g3", "Какой у меня тариф и баланс?", "cust_456")
    assert result.intent == "account_info"
    assert "pro" in result.answer.lower() or "1200" in result.answer


def test_run_chat_order_list():
    result = run_chat("g7", "Покажи все мои заказы", "cust_456")
    assert result.intent == "order_list"
    assert "#1" in result.answer or "shipped" in result.answer.lower()


def test_run_chat_billing():
    result = run_chat("g8", "Какие у меня счета?", "cust_456")
    assert result.intent == "billing"
    assert "1290" in result.answer or "pending" in result.answer.lower()


def test_run_chat_faq():
    result = run_chat("g9", "Сколько дней на возврат товара?", "cust_456")
    assert result.intent == "faq"
    assert "14" in result.answer


def test_run_chat_escalation():
    result = run_chat("g4", "Хочу возврат, сервис ужасный!", "cust_456")
    assert isinstance(result, dict)
    assert result["status"] == "awaiting_operator"
    assert result["interrupt"]["reason"]


def test_resume_after_escalation():
    run_chat("g5", "Хочу возврат, сервис ужасный!", "cust_456")
    response = resume_chat(
        "g5",
        operator_reply="Передаю менеджеру, вернёмся в течение 24ч",
        ticket_id="ZD-001",
    )
    assert response.escalated is True
    assert "24" in response.answer or "менеджер" in response.answer.lower()
    assert response.answer


def test_escalation_survives_graph_reset():
    """Simulates app restart: graph recompiled, checkpointer keeps HITL state."""
    result = run_chat("g6", "Хочу возврат, сервис ужасный!", "cust_456")
    assert result["status"] == "awaiting_operator"

    reset_graph()

    response = resume_chat(
        "g6",
        operator_reply="Оператор подключился, разберём возврат",
        ticket_id="ZD-002",
    )
    assert response.escalated is True
    assert response.answer
