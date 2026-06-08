from langchain_core.messages import HumanMessage

from app.graph import nodes
from app.graph.state import SupportState


def _state(message: str, **extra) -> SupportState:
    base: SupportState = {
        "session_id": "test-session",
        "tenant_id": "default",
        "customer_id": "cust_456",
        "messages": [HumanMessage(content=message)],
        "dialog_summary": extra.pop("dialog_summary", ""),
        "db_evidence": [],
        "rag_evidence": [],
        "citations": [],
        "draft_answer": "",
        "gaps": [],
        "escalated": False,
        "needs_interrupt": False,
        "intent": None,
        "active_agent": None,
        "sentiment": None,
        "extracted_order_id": None,
        "confidence": None,
        "escalation_reason": None,
        "ticket_id": None,
    }
    base.update(extra)  # type: ignore[typeddict-item]
    return base


def test_mock_classify_order_status():
    result = nodes.classify_intent(_state("Где мой заказ #1?"))
    assert result["intent"] == "order_status"
    assert result["extracted_order_id"] == 1


def test_mock_classify_account_info():
    result = nodes.classify_intent(_state("Какой у меня тариф и баланс?"))
    assert result["intent"] == "account_info"


def test_mock_classify_complaint():
    result = nodes.classify_intent(_state("Хочу возврат, сервис ужасный!"))
    assert result["intent"] == "complaint"
    assert result["sentiment"] == "negative"


def test_mock_classify_general():
    result = nodes.classify_intent(_state("Привет!"))
    assert result["intent"] == "general"
    assert result["sentiment"] == "positive"


def test_mock_classify_unclear():
    result = nodes.classify_intent(_state("ммм"))
    assert result["intent"] == "unclear"


def test_mock_classify_order_list():
    result = nodes.classify_intent(_state("Покажи все мои заказы"))
    assert result["intent"] == "order_list"


def test_mock_classify_billing():
    result = nodes.classify_intent(_state("Какие у меня счета?"))
    assert result["intent"] == "billing"


def test_mock_classify_faq():
    result = nodes.classify_intent(_state("Какая политика возврата?"))
    assert result["intent"] == "faq"


def test_search_knowledge_node():
    result = nodes.search_knowledge_node(_state("Сколько дней на возврат?", intent="faq"))
    assert result["rag_evidence"]
    assert result["citations"]


def test_check_escalation_on_complaint():
    state = _state(
        "жалоба",
        intent="complaint",
        sentiment="negative",
    )
    result = nodes.check_escalation(state)
    assert result["escalated"] is True
    assert result["needs_interrupt"] is True


def test_check_escalation_neutral_order():
    state = _state("заказ", intent="order_status", sentiment="neutral")
    result = nodes.check_escalation(state)
    assert result["escalated"] is False


def test_query_db_order_status():
    state = _state("заказ #1", intent="order_status", extracted_order_id=1)
    result = nodes.query_db(state)
    assert len(result["db_evidence"]) == 1
    assert result["db_evidence"][0]["data"]["status"] == "shipped"


def test_query_db_account_info():
    state = _state("баланс", intent="account_info")
    result = nodes.query_db(state)
    assert any(e["source_id"] == "customers" for e in result["db_evidence"])
    assert any(e["source_id"] == "orders" for e in result["db_evidence"])


def test_resolve_from_dialog_summary():
    state = _state(
        "Когда доставка?",
        intent="order_status",
        dialog_summary="вопрос по заказу #1",
    )
    result = nodes.resolve_from_dialog(state)
    assert result["db_evidence"]
    assert result["db_evidence"][0]["data"]["order_id"] == 1


def test_synthesize_answer_with_evidence():
    state = _state(
        "статус",
        intent="order_status",
        db_evidence=[
            {
                "source_type": "database",
                "source_id": "orders",
                "query": "order_id=1",
                "data": {
                    "order_id": 1,
                    "status": "shipped",
                    "delivery_date": "2025-06-10",
                },
            }
        ],
    )
    result = nodes.synthesize_answer(state)
    assert "shipped" in result["draft_answer"]
    assert result["confidence"] == "high"


def test_validate_answer_no_evidence():
    state = _state("заказ?", intent="order_status", db_evidence=[], draft_answer="...")
    result = nodes.validate_answer(state)
    assert result["confidence"] == "low"
    assert result["escalation_reason"] == "no_db_evidence_for_factual_query"
