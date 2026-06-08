from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.checkpointer import init_checkpointer, shutdown_checkpointer
from app.database import get_account_info, get_order_status, init_db, list_customer_orders
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
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=None)
def chat(request: ChatRequest):
    result = run_chat(
        session_id=request.session_id,
        message=request.message,
        customer_id=request.customer_id,
    )
    if isinstance(result, dict) and result.get("status") == "awaiting_operator":
        return result
    return result


@app.post("/chat/resume", response_model=ChatResponse)
def chat_resume(request: ResumeRequest):
    try:
        return resume_chat(
            session_id=request.session_id,
            operator_reply=request.operator_reply,
            ticket_id=request.ticket_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/demo/orders/{order_id}")
def demo_order(order_id: int, customer_id: str | None = None):
    data = get_order_status(order_id, customer_id)
    if not data:
        raise HTTPException(status_code=404, detail="Order not found")
    return data


@app.get("/demo/customers/{customer_id}")
def demo_customer(customer_id: str):
    data = get_account_info(customer_id)
    if not data:
        raise HTTPException(status_code=404, detail="Customer not found")
    orders = list_customer_orders(customer_id)
    return {"customer": data, "orders": orders}
