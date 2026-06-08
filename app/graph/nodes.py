import json
import re
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer

from app.async_session_store import aload_session, asave_session
from app.cached_db import get_cached_intent, set_cached_intent
from app.config import settings
from app.graph.state import SupportState
from app.integrations.zendesk import create_ticket
from app.prompts import get_prompt
from app.rag.retriever import search_knowledge
from app.schemas import DialogContext, IntentResult, SupportAnswer, ValidationResult
from app.tenant import DEFAULT_TENANT
from app.tools.registry import arun_tool


def _emit_answer_tokens(text: str, chunk_size: int = 16) -> None:
    try:
        writer = get_stream_writer()
    except Exception:
        return
    for index in range(0, len(text), chunk_size):
        writer({"type": "token", "text": text[index : index + chunk_size]})


def _stream_tokens_enabled(config: RunnableConfig | None) -> bool:
    if not config:
        return False
    configurable: dict[str, Any] = config.get("configurable", {})
    return bool(configurable.get("stream_tokens"))


def _stream_llm_synthesize(state: SupportState, evidence: list[dict], last_msg: str) -> dict:
    llm = _get_llm()
    prompt = get_prompt(
        "synthesize_answer_stream",
        message=last_msg,
        dialog_summary=state["dialog_summary"],
        evidence=json.dumps(evidence, ensure_ascii=False),
    )
    pieces: list[str] = []
    writer = get_stream_writer()
    for chunk in llm.stream(prompt):
        token = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
        if not token:
            continue
        pieces.append(token)
        writer({"type": "token", "text": token})
    answer = "".join(pieces).strip()
    return {"draft_answer": answer, "confidence": "medium", "gaps": []}


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


def _all_evidence(state: SupportState) -> list[dict]:
    return list(state.get("db_evidence", [])) + list(state.get("rag_evidence", []))


def _mock_classify(message: str) -> IntentResult:
    lower = message.lower()
    order_id = None
    match = re.search(r"#?\s*(\d+)", message)
    if match:
        order_id = int(match.group(1))

    if any(w in lower for w in ("жалоб", "ужас", "кошмар", "возврат")) and "политик" not in lower:
        if "хочу" in lower or "жалоб" in lower or "ужас" in lower or "кошмар" in lower:
            return IntentResult(intent="complaint", sentiment="negative", order_id=order_id)
    if any(
        w in lower
        for w in (
            "политик",
            "как оформить",
            "можно ли",
            "условия",
            "faq",
            "сколько дней",
            "гарант",
            "оператор",
            "связаться",
            "сколько стоит",
            "часы работ",
        )
    ):
        return IntentResult(intent="faq", sentiment="neutral", order_id=order_id)
    if any(w in lower for w in ("счёт", "счет", "оплат", "invoice", "платёж", "платеж", "счета")):
        return IntentResult(intent="billing", sentiment="neutral", order_id=order_id)
    if any(w in lower for w in ("список заказ", "все заказы", "мои заказы", "сколько заказов")):
        return IntentResult(intent="order_list", sentiment="neutral", order_id=order_id)
    if any(w in lower for w in ("заказ", "достав", "статус", "трек")):
        return IntentResult(intent="order_status", sentiment="neutral", order_id=order_id)
    if any(w in lower for w in ("аккаунт", "баланс", "тариф", "план", "профил")):
        return IntentResult(intent="account_info", sentiment="neutral", order_id=order_id)
    if any(w in lower for w in ("привет", "здравств", "спасибо")):
        return IntentResult(intent="general", sentiment="positive", order_id=order_id)
    return IntentResult(intent="unclear", sentiment="neutral", order_id=order_id)


async def load_session_node(state: SupportState) -> dict:
    tenant_id = state.get("tenant_id") or DEFAULT_TENANT
    stored = await aload_session(state["session_id"], tenant_id=tenant_id)
    customer_id = state.get("customer_id") or stored["customer_id"]
    return {
        "tenant_id": tenant_id,
        "dialog_summary": stored["summary"],
        "customer_id": customer_id,
    }


def classify_intent(state: SupportState) -> dict:
    last_msg = _last_user_message(state)
    summary = state.get("dialog_summary", "")

    cached = get_cached_intent(last_msg, summary)
    if cached is not None:
        return cached

    if settings.mock_llm or not settings.openai_api_key:
        result = _mock_classify(last_msg)
    else:
        llm = _get_llm()
        prompt = get_prompt(
            "classify_intent",
            dialog_summary=summary,
            message=last_msg,
        )
        result = llm.with_structured_output(IntentResult).invoke(prompt)

    payload = {
        "intent": result.intent,
        "sentiment": result.sentiment,
        "extracted_order_id": result.order_id,
    }
    set_cached_intent(last_msg, summary, payload)
    return payload


def check_escalation(state: SupportState) -> dict:
    if state["sentiment"] == "negative" and state["intent"] == "complaint":
        return {
            "escalated": True,
            "needs_interrupt": True,
            "escalation_reason": "negative_sentiment + complaint",
            "confidence": "low",
        }
    return {"escalated": False, "needs_interrupt": False}


async def query_db(state: SupportState) -> dict:
    intent = state["intent"]
    customer_id = state.get("customer_id")
    tenant_id = state.get("tenant_id") or DEFAULT_TENANT
    order_id = state.get("extracted_order_id")
    evidence: list[dict] = []

    if intent == "order_status" and order_id:
        data = await arun_tool(
            "get_order_status",
            order_id=order_id,
            customer_id=customer_id,
            tenant_id=tenant_id,
        )
        if data:
            evidence.append(
                {
                    "source_type": "database",
                    "source_id": "orders",
                    "query": f"order_id={order_id}",
                    "data": data,
                }
            )

    elif intent == "order_list" and customer_id:
        orders = await arun_tool(
            "list_customer_orders",
            customer_id=customer_id,
            tenant_id=tenant_id,
        )
        if orders:
            evidence.append(
                {
                    "source_type": "database",
                    "source_id": "orders",
                    "query": f"customer_id={customer_id}",
                    "data": orders,
                }
            )

    elif intent == "billing" and customer_id:
        invoices = await arun_tool(
            "list_customer_invoices",
            customer_id=customer_id,
            tenant_id=tenant_id,
        )
        if invoices:
            evidence.append(
                {
                    "source_type": "database",
                    "source_id": "invoices",
                    "query": f"customer_id={customer_id}",
                    "data": invoices,
                }
            )

    elif intent == "account_info" and customer_id:
        data = await arun_tool(
            "get_account_info",
            customer_id=customer_id,
            tenant_id=tenant_id,
        )
        if data:
            evidence.append(
                {
                    "source_type": "database",
                    "source_id": "customers",
                    "query": f"customer_id={customer_id}",
                    "data": data,
                }
            )
        orders = await arun_tool(
            "list_customer_orders",
            customer_id=customer_id,
            tenant_id=tenant_id,
        )
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


def search_knowledge_node(state: SupportState) -> dict:
    last_msg = _last_user_message(state)
    hits = search_knowledge(last_msg)
    citations = [
        {
            "source_type": "knowledge",
            "detail": f"{hit['title']} ({hit['source_id']}, score={hit['score']})",
        }
        for hit in hits
    ]
    return {"rag_evidence": hits, "citations": citations}


async def resolve_from_dialog(state: SupportState) -> dict:
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

    data = await arun_tool(
        "get_order_status",
        order_id=order_id,
        customer_id=state.get("customer_id"),
        tenant_id=state.get("tenant_id") or DEFAULT_TENANT,
    )
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


def _mock_synthesize(state: SupportState, evidence: list[dict]) -> dict:
    intent = state["intent"]
    if evidence and intent == "order_status":
        data = evidence[0]["data"]
        answer = (
            f"Заказ #{data['order_id']}: статус «{data['status']}». "
            f"Доставка ожидается {data.get('delivery_date') or 'уточняется'}."
        )
        return {"draft_answer": answer, "confidence": "high", "gaps": []}

    if evidence and intent == "order_list":
        orders = evidence[0]["data"]
        lines = [f"#{o['order_id']}: {o['status']}" for o in orders]
        return {
            "draft_answer": f"Ваши заказы: {', '.join(lines)}.",
            "confidence": "high",
            "gaps": [],
        }

    if evidence and intent == "billing":
        invoices = evidence[0]["data"]
        lines = [f"#{i['invoice_id']}: {i['amount']} ₽ ({i['status']})" for i in invoices]
        return {
            "draft_answer": f"Счета: {', '.join(lines)}.",
            "confidence": "high",
            "gaps": [],
        }

    if evidence and intent == "account_info":
        data = evidence[0]["data"]
        answer = (
            f"Аккаунт {data.get('name', data.get('customer_id'))}: "
            f"тариф {data.get('plan')}, баланс {data.get('balance')}."
        )
        return {"draft_answer": answer, "confidence": "high", "gaps": []}

    if evidence and intent == "faq":
        hits = state.get("rag_evidence", [])
        hit = max(hits, key=lambda item: item.get("score", 0)) if hits else {}
        text = hit.get("text", "")
        title = hit.get("title", "FAQ")
        return {
            "draft_answer": f"{title}: {text[:400]}",
            "confidence": "high",
            "gaps": [],
        }

    if intent == "general":
        return {
            "draft_answer": (
                "Здравствуйте! Чем могу помочь? "
                "Могу проверить статус заказа, счета или ответить на FAQ."
            ),
            "confidence": "high",
            "gaps": [],
        }

    return {
        "draft_answer": "Не нашёл данные в системе. Уточните номер заказа или вопрос.",
        "confidence": "low",
        "gaps": [],
    }


def synthesize_answer(state: SupportState, config: RunnableConfig | None = None) -> dict:
    last_msg = _last_user_message(state)
    evidence = _all_evidence(state)
    stream_tokens = _stream_tokens_enabled(config)

    if settings.mock_llm or not settings.openai_api_key:
        result = _mock_synthesize(state, evidence)
        if stream_tokens:
            _emit_answer_tokens(result["draft_answer"])
        return result

    if stream_tokens:
        return _stream_llm_synthesize(state, evidence, last_msg)

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

    if state["intent"] == "faq" and not state.get("rag_evidence"):
        return {
            "confidence": "low",
            "escalation_reason": "no_rag_evidence_for_faq",
        }

    if state["intent"] in ("order_status", "account_info", "order_list", "billing"):
        if not state.get("db_evidence"):
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
            evidence=_all_evidence(state),
        )
    )
    if not check.grounded:
        return {"confidence": "low", "escalation_reason": check.reason}
    return {}


def clarify(state: SupportState) -> dict:
    if settings.mock_llm or not settings.openai_api_key:
        return {
            "draft_answer": "Уточните: номер заказа, вопрос по счёту или FAQ?",
            "confidence": "medium",
        }
    llm = _get_llm()
    reply = llm.invoke(get_prompt("clarify", message=_last_user_message(state))).content
    return {"draft_answer": reply, "confidence": "medium"}


def escalate(state: SupportState) -> dict:
    from langgraph.types import interrupt

    ticket_id = create_ticket(
        session_id=state["session_id"],
        customer_id=state.get("customer_id"),
        reason=state.get("escalation_reason", "escalation"),
        transcript=[m.content for m in state["messages"]],
    )

    payload = interrupt(
        {
            "reason": state.get("escalation_reason", "escalation"),
            "transcript": [m.content for m in state["messages"]],
            "dialog_summary": state.get("dialog_summary", ""),
            "draft_answer": state.get("draft_answer", ""),
            "customer_id": state.get("customer_id"),
            "db_evidence": state.get("db_evidence", []),
            "ticket_id": ticket_id,
        }
    )
    return {
        "draft_answer": payload.get("operator_reply", state.get("draft_answer", "")),
        "escalated": True,
        "ticket_id": payload.get("ticket_id") or ticket_id,
        "needs_interrupt": False,
    }


async def save_session_node(state: SupportState) -> dict:
    tenant_id = state.get("tenant_id") or DEFAULT_TENANT
    stored = await aload_session(state["session_id"], tenant_id=tenant_id)
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

    await asave_session(
        session_id=state["session_id"],
        customer_id=state.get("customer_id"),
        summary=summary,
        messages=messages[-20:],
        tenant_id=tenant_id,
        status=status,
        ticket_id=state.get("ticket_id"),
    )
    return {"dialog_summary": summary}
