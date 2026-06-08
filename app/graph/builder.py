from langgraph.graph import END, START, StateGraph

from app.checkpointer import get_checkpointer
from app.graph import nodes
from app.graph.state import SupportState

DB_INTENTS = ("order_status", "order_list", "billing", "account_info")


def route_after_escalation_check(state: SupportState) -> str:
    if state.get("escalated"):
        return "escalate"
    intent = state.get("intent")
    if intent == "unclear":
        return "clarify"
    if intent in DB_INTENTS:
        return "query_db"
    if intent == "faq":
        return "search_knowledge"
    if intent == "complaint":
        return "escalate"
    return "synthesize_answer"


def route_after_validate(state: SupportState) -> str:
    if state.get("confidence") == "low":
        return "escalate"
    if state.get("confidence") == "medium" and state.get("intent") == "unclear":
        return "clarify"
    return "save_session"


def build_graph():
    graph = StateGraph(SupportState)

    graph.add_node("load_session", nodes.load_session_node)
    graph.add_node("classify_intent", nodes.classify_intent)
    graph.add_node("check_escalation", nodes.check_escalation)
    graph.add_node("query_db", nodes.query_db)
    graph.add_node("search_knowledge", nodes.search_knowledge_node)
    graph.add_node("resolve_from_dialog", nodes.resolve_from_dialog)
    graph.add_node("synthesize_answer", nodes.synthesize_answer)
    graph.add_node("validate_answer", nodes.validate_answer)
    graph.add_node("clarify", nodes.clarify)
    graph.add_node("escalate", nodes.escalate)
    graph.add_node("save_session", nodes.save_session_node)

    graph.add_edge(START, "load_session")
    graph.add_edge("load_session", "classify_intent")
    graph.add_edge("classify_intent", "check_escalation")
    graph.add_conditional_edges("check_escalation", route_after_escalation_check)

    graph.add_edge("query_db", "resolve_from_dialog")
    graph.add_edge("resolve_from_dialog", "synthesize_answer")
    graph.add_edge("search_knowledge", "synthesize_answer")
    graph.add_edge("synthesize_answer", "validate_answer")
    graph.add_conditional_edges("validate_answer", route_after_validate)

    graph.add_edge("clarify", "save_session")
    graph.add_edge("escalate", "save_session")
    graph.add_edge("save_session", END)

    checkpointer = get_checkpointer()
    return graph.compile(checkpointer=checkpointer)
