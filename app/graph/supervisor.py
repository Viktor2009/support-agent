from app.graph.state import IntentType, SupportState

AgentName = str

INTENT_TO_AGENT: dict[IntentType, AgentName] = {
    "order_status": "orders_agent",
    "order_list": "orders_agent",
    "billing": "billing_agent",
    "account_info": "billing_agent",
    "faq": "knowledge_agent",
    "general": "general_agent",
    "unclear": "general_agent",
    "complaint": "escalation_agent",
}


def supervisor_node(state: SupportState) -> dict:
    intent = state.get("intent") or "unclear"
    return {"active_agent": INTENT_TO_AGENT.get(intent, "general_agent")}
