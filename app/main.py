from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.admin_routes import router as admin_router
from app.auth import AuthContext, get_auth_context, resolve_customer_id
from app.cache import init_cache, shutdown_cache
from app.checkpointer import init_checkpointer, shutdown_checkpointer
from app.config import parse_cors_origins, settings
from app.database import (
    get_account_info,
    get_order_status,
    init_db,
    list_customer_orders,
    save_feedback,
)
from app.health import build_health_payload
from app.rate_limit import RateLimitMiddleware
from app.schemas import ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse, ResumeRequest
from app.service import resume_chat, run_chat


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    init_cache()
    init_checkpointer()
    yield
    shutdown_checkpointer()
    shutdown_cache()


app = FastAPI(
    title="Support Agent API",
    description="Minimal FastAPI + LangGraph support agent (DB + dialog)",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

_root = Path(__file__).resolve().parent.parent
for mount_path, folder in (("/widget", "widget"), ("/admin-ui", "admin")):
    directory = _root / folder
    if directory.exists():
        app.mount(mount_path, StaticFiles(directory=directory, html=True), name=folder)

app.include_router(admin_router)


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


@app.post("/chat/feedback", response_model=FeedbackResponse)
def chat_feedback(
    request: FeedbackRequest,
    auth: AuthContext | None = Depends(get_auth_context),
):
    customer_id = resolve_customer_id(auth, request.customer_id)
    result = save_feedback(
        session_id=request.session_id,
        rating=request.rating,
        customer_id=customer_id,
        comment=request.comment,
    )
    return FeedbackResponse(**result)


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
