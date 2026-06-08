from typing import Annotated, Literal, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class SupportState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    session_id: str
    customer_id: Optional[str]
    dialog_summary: str

    intent: Optional[Literal["order_status", "account_info", "general", "complaint", "unclear"]]
    sentiment: Optional[Literal["positive", "neutral", "negative"]]
    extracted_order_id: Optional[int]

    db_evidence: list[dict]
    citations: list[dict]

    draft_answer: str
    confidence: Optional[Literal["high", "medium", "low"]]
    gaps: list[str]

    escalated: bool
    escalation_reason: Optional[str]
    ticket_id: Optional[str]
    needs_interrupt: bool
