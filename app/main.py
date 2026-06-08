from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth import AuthContext, get_auth_context, resolve_customer_id
from app.checkpointer import init_checkpointer, shutdown_checkpointer
from app.config import parse_cors_origins, settings
from app.database import get_account_info, get_order_status, init_db, list_customer_orders
from app.health import build_health_payload
from app.schemas import ChatRequest, ChatResponse, ResumeRequest
from app.service import resume_chat, run_chat


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    init_checkpointer()
    yield
    shutdown_checkpointer()


app = FastAPI(
    title="Support Agent API",
    description="Minimal FastAPI + LangGraph support agent (DB + dialog)",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return build_health_payload()


@app.post("/chat", response_model=None)
def chat(
    request: ChatRequest,
    auth: AuthContext | None = Depends(get_auth_context),
):
    customer_id = resolve_customer_id(auth, request.customer_id)
    result = run_chat(
        session_id=request.session_id,
        message=request.message,
        customer_id=customer_id,
    )
    if isinstance(result, dict) and result.get("status") == "awaiting_operator":
        return result
    return result


@app.post("/chat/resume", response_model=ChatResponse)
def chat_resume(
    request: ResumeRequest,
    _: AuthContext | None = Depends(get_auth_context),
):
    try:
        return resume_chat(
            session_id=request.session_id,
            operator_reply=request.operator_reply,
            ticket_id=request.ticket_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/demo/orders/{order_id}")
def demo_order(
    order_id: int,
    customer_id: str | None = None,
    auth: AuthContext | None = Depends(get_auth_context),
):
    if auth is not None:
        customer_id = auth.customer_id
    data = get_order_status(order_id, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail="Order not found")
    return data


@app.get("/demo/customers/{customer_id}")
def demo_customer(
    customer_id: str,
    auth: AuthContext | None = Depends(get_auth_context),
):
    if auth is not None:
        customer_id = auth.customer_id
    data = get_account_info(customer_id)
    if not data:
        raise HTTPException(status_code=404, detail="Customer not found")
    orders = list_customer_orders(customer_id)
    return {"customer": data, "orders": orders}
