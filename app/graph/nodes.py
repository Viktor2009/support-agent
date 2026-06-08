import json
import re

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.database import get_account_info, get_order_status, list_customer_orders
from app.graph.state import SupportState
from app.prompts import get_prompt
from app.schemas import DialogContext, IntentResult, SupportAnswer, ValidationResult
from app.session_store import load_session, save_session


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key or "mock",
        temperature=0,
    )


def _last_user_message(state: SupportState) -> str:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message.content
    return ""


def _mock_classify(message: str) -> IntentResult:
    lower = message.lower()
    order_id = None
    match = re.search(r"#?\s*(\d+)", message)
    if match:
        order_id = int(match.group(1))

    if any(w in lower for w in ("жалоб", "вернут", "возврат", "ужас", "кошмар")):
        return IntentResult(intent="complaint", sentiment="negative", order_id=order_id)
    if any(w in lower for w in ("заказ", "достав", "статус", "трек")):
        return IntentResult(intent="order_status", sentiment="neutral", order_id=order_id)
    if any(w in lower for w in ("аккаунт", "баланс", "тариф", "план", "профил")):
        return IntentResult(intent="account_info", sentiment="neutral", order_id=order_id)
    if any(w in lower for w in ("привет", "здравств", "спасибо")):
        return IntentResult(intent="general", sentiment="positive", order_id=order_id)
    return IntentResult(intent="unclear", sentiment="neutral", order_id=order_id)


def load_session_node(state: SupportState) -> dict:
    stored = load_session(state["session_id"])
    customer_id = state.get("customer_id") or stored["customer_id"]
    return {
        "dialog_summary": stored["summary"],
        "customer_id": customer_id,
    }


def classify_intent(state: SupportState) -> dict:
    last_msg = _last_user_message(state)

    if settings.mock_llm or not settings.openai_api_key:
        result = _mock_classify(last_msg)
    else:
        llm = _get_llm()
        prompt = get_prompt(
            "classify_intent",
            dialog_summary=state["dialog_summary"],
            message=last_msg,
        )
        result = llm.with_structured_output(IntentResult).invoke(prompt)

    return {
        "intent": result.intent,
        "sentiment": result.sentiment,
        "extracted_order_id": result.order_id,
    }


def check_escalation(state: SupportState) -> dict:
    if state["sentiment"] == "negative" and state["intent"] == "complaint":
        return {
            "escalated": True,
            "needs_interrupt": True,
            "escalation_reason": "negative_sentiment + complaint",
            "confidence": "low",
        }
    return {"escalated": False, "needs_interrupt": False}


def query_db(state: SupportState) -> dict:
    intent = state["intent"]
    customer_id = state.get("customer_id")
    order_id = state.get("extracted_order_id")
    evidence: list[dict] = []

    if intent == "order_status" and order_id:
        data = get_order_status(order_id, customer_id)
        if data:
            evidence.append(
                {
                    "source_type": "database",
                    "source_id": "orders",
                    "query": f"order_id={order_id}",
                    "data": data,
                }
            )

    elif intent == "account_info" and customer_id:
        data = get_account_info(customer_id)
        if data:
            evidence.append(
                {
                    "source_type": "database",
                    "source_id": "customers",
                    "query": f"customer_id={customer_id}",
                    "data": data,
                }
            )
        orders = list_customer_orders(customer_id)
        if orders:
            evidence.append(
                {
                    "source_type": "database",
                    "source_id": "orders",
                    "query": f"customer_id={customer_id}",
                    "data": orders,
                }
            )

    return {"db_evidence": evidence}


def resolve_from_dialog(state: SupportState) -> dict:
    if state.get("db_evidence") or state["intent"] != "order_status":
        return {}

    if settings.mock_llm or not settings.openai_api_key:
        summary = state["dialog_summary"]
        match = re.search(r"#?\s*(\d+)", summary)
        if not match:
            return {}
        order_id = int(match.group(1))
        inferred_from = f"order_id={order_id} из summary диалога"
    else:
        llm = _get_llm()
        ctx = llm.with_structured_output(DialogContext).invoke(
            get_prompt(
                "resolve_from_dialog",
                dialog_summary=state["dialog_summary"],
                messages=[m.content for m in state["messages"][-4:]],
            )
        )
        if not ctx.order_id:
            return {}
        order_id = ctx.order_id
        inferred_from = ctx.inferred_from

    data = get_order_status(order_id, state.get("customer_id"))
    if not data:
        return {}

    return {
        "db_evidence": [
            {
                "source_type": "database",
                "source_id": "orders",
                "query": f"order_id={order_id}",
                "data": data,
            }
        ],
        "citations": [
            {
                "source_type": "dialog",
                "detail": inferred_from,
            }
        ],
    }


def synthesize_answer(state: SupportState) -> dict:
    last_msg = _last_user_message(state)
    evidence = state.get("db_evidence", [])

    if settings.mock_llm or not settings.openai_api_key:
        if evidence:
            data = evidence[0]["data"]
            if state["intent"] == "order_status":
                answer = (
                    f"Заказ #{data['order_id']}: статус «{data['status']}». "
                    f"Доставка ожидается {data.get('delivery_date') or 'уточняется'}."
                )
                confidence = "high"
            else:
                answer = (
                    f"Аккаунт {data.get('name', data.get('customer_id'))}: "
                    f"тариф {data.get('plan')}, баланс {data.get('balance')}."
                )
                confidence = "high"
        elif state["intent"] == "general":
            answer = (
                "Здравствуйте! Чем могу помочь? "
                "Могу проверить статус заказа или данные аккаунта."
            )
            confidence = "high"
        else:
            answer = "Не нашёл данные в системе. Уточните номер заказа или customer_id."
            confidence = "low"
        return {"draft_answer": answer, "confidence": confidence, "gaps": []}

    llm = _get_llm()
    result = llm.with_structured_output(SupportAnswer).invoke(
        get_prompt(
            "synthesize_answer",
            message=last_msg,
            dialog_summary=state["dialog_summary"],
            evidence=json.dumps(evidence, ensure_ascii=False),
        )
    )
    return {
        "draft_answer": result.answer,
        "confidence": result.confidence,
        "gaps": result.gaps,
    }


def validate_answer(state: SupportState) -> dict:
    if state["intent"] == "general":
        return {}

    if state["intent"] in ("order_status", "account_info") and not state.get("db_evidence"):
        return {
            "confidence": "low",
            "escalation_reason": "no_db_evidence_for_factual_query",
        }

    if settings.mock_llm or not settings.openai_api_key:
        return {}

    llm = _get_llm()
    check = llm.with_structured_output(ValidationResult).invoke(
        get_prompt(
            "validate_answer",
            draft_answer=state["draft_answer"],
            evidence=state.get("db_evidence", []),
        )
    )
    if not check.grounded:
        return {"confidence": "low", "escalation_reason": check.reason}
    return {}


def clarify(state: SupportState) -> dict:
    if settings.mock_llm or not settings.openai_api_key:
        return {
            "draft_answer": "Уточните, пожалуйста: номер заказа или вопрос по аккаунту?",
            "confidence": "medium",
        }
    llm = _get_llm()
    reply = llm.invoke(get_prompt("clarify", message=_last_user_message(state))).content
    return {"draft_answer": reply, "confidence": "medium"}


def escalate(state: SupportState) -> dict:
    from langgraph.types import interrupt

    payload = interrupt(
        {
            "reason": state.get("escalation_reason", "escalation"),
            "transcript": [m.content for m in state["messages"]],
            "dialog_summary": state.get("dialog_summary", ""),
            "draft_answer": state.get("draft_answer", ""),
            "customer_id": state.get("customer_id"),
            "db_evidence": state.get("db_evidence", []),
        }
    )
    return {
        "draft_answer": payload.get("operator_reply", state.get("draft_answer", "")),
        "escalated": True,
        "ticket_id": payload.get("ticket_id"),
        "needs_interrupt": False,
    }


def save_session_node(state: SupportState) -> dict:
    stored = load_session(state["session_id"])
    messages = list(stored["messages"])
    messages.append({"role": "user", "content": _last_user_message(state)})
    if state.get("draft_answer"):
        messages.append({"role": "assistant", "content": state["draft_answer"]})

    summary = state.get("dialog_summary", "")
    if settings.mock_llm or not settings.openai_api_key:
        if messages:
            summary = " | ".join(m["content"][:80] for m in messages[-4:])
    elif len(messages) >= 6 and settings.openai_api_key:
        llm = _get_llm()
        summary = llm.invoke(
            get_prompt("summarize_dialog", messages=messages[-6:])
        ).content

    status = "awaiting_operator" if state.get("needs_interrupt") else "active"
    if state.get("escalated") and not state.get("needs_interrupt"):
        status = "closed"

    save_session(
        session_id=state["session_id"],
        customer_id=state.get("customer_id"),
        summary=summary,
        messages=messages[-20:],
        status=status,
        ticket_id=state.get("ticket_id"),
    )
    return {"dialog_summary": summary}
