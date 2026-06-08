from collections.abc import Iterator

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.checkpointer import reset_checkpointer
from app.graph.builder import build_graph
from app.graph.state import SupportState
from app.metrics import MetricsMiddleware, record_escalation
from app.observability import graph_invoke_config
from app.schemas import ChatResponse, Citation
from app.sse import format_sse
from app.tenant import DEFAULT_TENANT

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
        active_agent=state.get("active_agent"),
        tenant_id=state.get("tenant_id"),
        citations=citations,
        escalated=state.get("escalated", False),
        escalation_reason=state.get("escalation_reason"),
        gaps=state.get("gaps", []),
    )


def _build_input_state(
    session_id: str,
    message: str,
    customer_id: str | None,
    *,
    tenant_id: str | None = None,
) -> SupportState:
    return {
        "session_id": session_id,
        "tenant_id": tenant_id or DEFAULT_TENANT,
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
        "active_agent": None,
        "sentiment": None,
        "extracted_order_id": None,
        "confidence": None,
        "escalation_reason": None,
        "ticket_id": None,
    }


def _interrupt_payload(graph, config) -> dict | None:
    snapshot = graph.get_state(config)
    if not snapshot.tasks:
        return None
    for task in snapshot.tasks:
        if task.interrupts:
            return task.interrupts[0].value
    return None


def run_chat(
    session_id: str,
    message: str,
    customer_id: str | None,
    *,
    tenant_id: str | None = None,
) -> ChatResponse | dict:
    graph = get_graph()
    config = graph_invoke_config(session_id)
    input_state = _build_input_state(session_id, message, customer_id, tenant_id=tenant_id)

    result = graph.invoke(input_state, config=config)
    interrupt_payload = _interrupt_payload(graph, config)
    if interrupt_payload is not None:
        record_escalation()
        snapshot = graph.get_state(config)
        return {
            "status": "awaiting_operator",
            "interrupt": interrupt_payload,
            "partial_state": snapshot.values,
            "session_id": session_id,
        }

    return _to_response(result)


def stream_chat(
    session_id: str,
    message: str,
    customer_id: str | None,
    *,
    tenant_id: str | None = None,
    token_chunk_size: int = 24,
) -> Iterator[str]:
    graph = get_graph()
    config = graph_invoke_config(session_id, stream_tokens=True)
    input_state = _build_input_state(session_id, message, customer_id, tenant_id=tenant_id)
    final_state: SupportState | None = None
    tokens_streamed = False

    for mode, chunk in graph.stream(
        input_state,
        config=config,
        stream_mode=["updates", "values", "custom"],
    ):
        if mode == "custom":
            if isinstance(chunk, dict) and chunk.get("type") == "token":
                tokens_streamed = True
                yield format_sse("token", {"text": chunk.get("text", "")})
            continue
        if mode == "updates":
            for node_name, update in chunk.items():
                if not update:
                    continue
                payload: dict = {"node": node_name}
                for key in ("intent", "active_agent", "sentiment", "confidence"):
                    if key in update:
                        payload[key] = update[key]
                yield format_sse("node", payload)
        elif mode == "values":
            final_state = chunk

    interrupt_payload = _interrupt_payload(graph, config)
    if interrupt_payload is not None:
        record_escalation()
        snapshot = graph.get_state(config)
        yield format_sse(
            "interrupt",
            {
                "status": "awaiting_operator",
                "interrupt": interrupt_payload,
                "session_id": session_id,
                "partial_state": snapshot.values,
            },
        )
        return

    if final_state is None:
        yield format_sse("error", {"detail": "Graph produced no final state"})
        return

    answer = final_state.get("draft_answer", "")
    if not tokens_streamed:
        for index in range(0, len(answer), token_chunk_size):
            yield format_sse("token", {"text": answer[index : index + token_chunk_size]})

    response = _to_response(final_state)
    yield format_sse("done", response.model_dump())


def resume_chat(session_id: str, operator_reply: str, ticket_id: str | None = None) -> ChatResponse:
    graph = get_graph()
    config = graph_invoke_config(session_id)

    result = graph.invoke(
        Command(resume={"operator_reply": operator_reply, "ticket_id": ticket_id}),
        config=config,
    )
    return _to_response(result)
