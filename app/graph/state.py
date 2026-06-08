from typing import Annotated, Literal, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

IntentType = Literal[
    "order_status",
    "order_list",
    "billing",
    "faq",
    "account_info",
    "general",
    "complaint",
    "unclear",
]


class SupportState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    session_id: str
    tenant_id: Optional[str]
    customer_id: Optional[str]
    dialog_summary: str

    intent: Optional[IntentType]
    active_agent: Optional[str]
    sentiment: Optional[Literal["positive", "neutral", "negative"]]
    extracted_order_id: Optional[int]

    db_evidence: list[dict]
    rag_evidence: list[dict]
    citations: list[dict]

    draft_answer: str
    confidence: Optional[Literal["high", "medium", "low"]]
    gaps: list[str]

    escalated: bool
    escalation_reason: Optional[str]
    ticket_id: Optional[str]
    needs_interrupt: bool
