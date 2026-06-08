from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., examples=["session-abc123"])
    message: str = Field(..., examples=["Где мой заказ #1?"])
    customer_id: Optional[str] = Field(None, examples=["cust_456"])


class Citation(BaseModel):
    source_type: str
    detail: str


class ChatResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    confidence: Optional[str] = None
    citations: list[Citation] = Field(default_factory=list)
    escalated: bool = False
    escalation_reason: Optional[str] = None
    gaps: list[str] = Field(default_factory=list)


class ResumeRequest(BaseModel):
    session_id: str
    operator_reply: str
    ticket_id: Optional[str] = None


class IntentResult(BaseModel):
    intent: Literal[
        "order_status",
        "order_list",
        "billing",
        "faq",
        "account_info",
        "general",
        "complaint",
        "unclear",
    ]
    sentiment: Literal["positive", "neutral", "negative"]
    order_id: Optional[int] = None


class DialogContext(BaseModel):
    order_id: Optional[int] = None
    inferred_from: str = ""


class SupportAnswer(BaseModel):
    answer: str
    confidence: Literal["high", "medium", "low"]
    gaps: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    grounded: bool
    reason: str = ""
