from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.admin_routes import router as admin_router
from app.async_database import dispose_async_db, init_async_db
from app.auth import AuthContext, get_auth_context, resolve_customer_id, resolve_tenant_id
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
from app.executor import run_sync
from app.gdpr_routes import router as gdpr_router
from app.health import build_health_payload
from app.metrics import MetricsMiddleware, metrics_content_type, metrics_payload
from app.rate_limit import RateLimitMiddleware
from app.schemas import ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse, ResumeRequest
from app.security import SecurityHeadersMiddleware
from app.service import resume_chat, run_chat, stream_chat
from app.rag.index import warm_index
from app.tools import bootstrap_tools


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    init_async_db()
    bootstrap_tools()
    init_cache()
    init_checkpointer()
    warm_index()
    yield
    await dispose_async_db()
    shutdown_checkpointer()
    shutdown_cache()


app = FastAPI(
    title="Support Agent API",
    description="Minimal FastAPI + LangGraph support agent (DB + dialog)",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)
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
app.include_router(gdpr_router)


@app.get("/health")
async def health():
    return await build_health_payload()


@app.get("/metrics")
async def metrics():
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return Response(content=metrics_payload(), media_type=metrics_content_type())


@app.post("/chat", response_model=None)
async def chat(
    request: ChatRequest,
    auth: AuthContext | None = Depends(get_auth_context),
):
    customer_id = resolve_customer_id(auth, request.customer_id)
    tenant_id = resolve_tenant_id(auth, request.tenant_id)
    result = await run_sync(
        run_chat,
        session_id=request.session_id,
        message=request.message,
        customer_id=customer_id,
        tenant_id=tenant_id,
    )
    if isinstance(result, dict) and result.get("status") == "awaiting_operator":
        return result
    return result


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    auth: AuthContext | None = Depends(get_auth_context),
):
    customer_id = resolve_customer_id(auth, request.customer_id)
    tenant_id = resolve_tenant_id(auth, request.tenant_id)
    return StreamingResponse(
        stream_chat(
            session_id=request.session_id,
            message=request.message,
            customer_id=customer_id,
            tenant_id=tenant_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/chat/resume", response_model=ChatResponse)
async def chat_resume(
    request: ResumeRequest,
    _: AuthContext | None = Depends(get_auth_context),
):
    try:
        return await run_sync(
            resume_chat,
            session_id=request.session_id,
            operator_reply=request.operator_reply,
            ticket_id=request.ticket_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat/feedback", response_model=FeedbackResponse)
async def chat_feedback(
    request: FeedbackRequest,
    auth: AuthContext | None = Depends(get_auth_context),
):
    customer_id = resolve_customer_id(auth, request.customer_id)
    tenant_id = resolve_tenant_id(auth, request.tenant_id)
    result = await run_sync(
        save_feedback,
        session_id=request.session_id,
        rating=request.rating,
        customer_id=customer_id,
        comment=request.comment,
        tenant_id=tenant_id,
    )
    return FeedbackResponse(**result)


@app.get("/demo/orders/{order_id}")
async def demo_order(
    order_id: int,
    customer_id: str | None = None,
    auth: AuthContext | None = Depends(get_auth_context),
):
    if auth is not None:
        customer_id = auth.customer_id
        tenant_id = auth.tenant_id
    else:
        tenant_id = "default"
    data = await run_sync(
        get_order_status,
        order_id,
        customer_id,
        tenant_id=tenant_id,
    )
    if not data:
        raise HTTPException(status_code=404, detail="Order not found")
    return data


@app.get("/demo/customers/{customer_id}")
async def demo_customer(
    customer_id: str,
    auth: AuthContext | None = Depends(get_auth_context),
):
    if auth is not None:
        customer_id = auth.customer_id
        tenant_id = auth.tenant_id
    else:
        tenant_id = "default"
    data = await run_sync(get_account_info, customer_id, tenant_id=tenant_id)
    if not data:
        raise HTTPException(status_code=404, detail="Customer not found")
    orders = await run_sync(list_customer_orders, customer_id, tenant_id=tenant_id)
    return {"customer": data, "orders": orders}
