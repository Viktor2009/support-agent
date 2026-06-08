from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.checkpointer import reset_checkpointer
from app.graph.builder import build_graph
from app.graph.state import SupportState
from app.observability import graph_invoke_config
from app.schemas import ChatResponse, Citation

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def reset_graph() -> None:
    """Reset compiled graph (simulates app restart; checkpointer persists)."""
    global _graph
    _graph = None


def reset_all() -> None:
    """Reset graph and checkpointer (for test isolation)."""
    reset_graph()
    reset_checkpointer()


def _to_response(state: SupportState) -> ChatResponse:
    citations = [
        Citation(
            source_type=c.get("source_type", "unknown"),
            detail=c.get("detail", c.get("query", "")),
        )
        for c in state.get("citations", [])
    ]
    for item in state.get("db_evidence", []):
        citations.append(
            Citation(
                source_type="database",
                detail=f"{item['source_id']}: {item['query']}",
            )
        )

    for item in state.get("rag_evidence", []):
        title = item.get("title", item.get("source_id", "faq"))
        snippet = item.get("text", "")[:120]
        citations.append(
            Citation(
                source_type="knowledge",
                detail=f"{title}: {snippet}",
            )
        )

    return ChatResponse(
        answer=state.get("draft_answer", ""),
        intent=state.get("intent"),
        sentiment=state.get("sentiment"),
        confidence=state.get("confidence"),
        citations=citations,
        escalated=state.get("escalated", False),
        escalation_reason=state.get("escalation_reason"),
        gaps=state.get("gaps", []),
    )


def run_chat(session_id: str, message: str, customer_id: str | None) -> ChatResponse | dict:
    graph = get_graph()
    config = graph_invoke_config(session_id)

    input_state: SupportState = {
        "session_id": session_id,
        "customer_id": customer_id,
        "messages": [HumanMessage(content=message)],
        "dialog_summary": "",
        "db_evidence": [],
        "rag_evidence": [],
        "citations": [],
        "draft_answer": "",
        "gaps": [],
        "escalated": False,
        "needs_interrupt": False,
        "intent": None,
        "sentiment": None,
        "extracted_order_id": None,
        "confidence": None,
        "escalation_reason": None,
        "ticket_id": None,
    }

    result = graph.invoke(input_state, config=config)
    snapshot = graph.get_state(config)

    if snapshot.tasks:
        interrupt_payload = None
        for task in snapshot.tasks:
            if task.interrupts:
                interrupt_payload = task.interrupts[0].value
                break
        return {
            "status": "awaiting_operator",
            "interrupt": interrupt_payload,
            "partial_state": snapshot.values,
            "session_id": session_id,
        }

    return _to_response(result)


def resume_chat(session_id: str, operator_reply: str, ticket_id: str | None = None) -> ChatResponse:
    graph = get_graph()
    config = graph_invoke_config(session_id)

    result = graph.invoke(
        Command(resume={"operator_reply": operator_reply, "ticket_id": ticket_id}),
        config=config,
    )
    return _to_response(result)
