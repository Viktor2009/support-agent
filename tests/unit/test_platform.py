from app.graph.supervisor import supervisor_node
from app.privacy import mask_email, mask_pii_text, mask_payload
from app.tools import bootstrap_tools
from app.tools.registry import list_tools, run_tool


def test_supervisor_maps_intent_to_agent():
    result = supervisor_node({"intent": "order_status"})
    assert result["active_agent"] == "orders_agent"

    billing = supervisor_node({"intent": "billing"})
    assert billing["active_agent"] == "billing_agent"

    faq = supervisor_node({"intent": "faq"})
    assert faq["active_agent"] == "knowledge_agent"


def test_tools_registry_bootstrap(isolated_env):
    bootstrap_tools()
    names = list_tools()
    assert "get_order_status" in names
    data = run_tool("get_order_status", order_id=1, customer_id="cust_456", tenant_id="default")
    assert data["status"] == "shipped"


def test_privacy_mask_email():
    assert mask_email("ivan@example.com") == "i***@example.com"


def test_privacy_mask_text():
    masked = mask_pii_text("Пишите на ivan@example.com или +7 999 123-45-67")
    assert "@" in masked
    assert "ivan@example.com" not in masked
    assert "[PHONE]" in masked


def test_privacy_mask_payload():
    payload = {"email": "a@b.com", "nested": [{"note": "call +79991234567"}]}
    masked = mask_payload(payload)
    assert "a@b.com" not in str(masked)
    assert "[PHONE]" in str(masked)
