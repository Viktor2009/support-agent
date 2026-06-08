from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.cached_db import (
    get_cached_order,
    get_cached_orders_list,
    set_cached_order,
    set_cached_orders_list,
)
from app.config import settings
from app.tenant import DEFAULT_TENANT


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    tenant_id = Column(String, primary_key=True, default=DEFAULT_TENANT)
    customer_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    plan = Column(String, nullable=False)
    balance = Column(Float, default=0.0)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, default=DEFAULT_TENANT)
    customer_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    ship_date = Column(String, nullable=True)
    delivery_date = Column(String, nullable=True)
    total = Column(Float, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, default=DEFAULT_TENANT)
    customer_id = Column(String, nullable=False)
    order_id = Column(Integer, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    due_date = Column(String, nullable=True)


class ChatSession(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, default=DEFAULT_TENANT)
    customer_id = Column(String, nullable=True)
    summary = Column(Text, default="")
    messages = Column(JSON, default=list)
    status = Column(String, default="active")
    ticket_id = Column(String, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, default=DEFAULT_TENANT)
    session_id = Column(String, nullable=False)
    customer_id = Column(String, nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def reset_engine(url: str | None = None) -> None:
    """Recreate engine from current settings or explicit URL (for tests)."""
    global engine, SessionLocal
    db_url = url or settings.database_url
    if engine is not None:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
    engine = create_engine(db_url, **_engine_kwargs(db_url))
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def configure_database(url: str) -> None:
    """Point app at a new database URL and recreate schema."""
    settings.database_url = url
    reset_engine(url)
    init_db()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(Customer).count() == 0:
            db.add_all(
                [
                    Customer(
                        tenant_id=DEFAULT_TENANT,
                        customer_id="cust_456",
                        name="Иван Петров",
                        email="ivan@example.com",
                        plan="pro",
                        balance=1200.0,
                    ),
                    Customer(
                        tenant_id=DEFAULT_TENANT,
                        customer_id="cust_789",
                        name="Мария Сидорова",
                        email="maria@example.com",
                        plan="basic",
                        balance=0.0,
                    ),
                    Customer(
                        tenant_id="acme",
                        customer_id="cust_acme",
                        name="ACME Corp",
                        email="billing@acme.example",
                        plan="enterprise",
                        balance=5000.0,
                    ),
                ]
            )
            db.add_all(
                [
                    Order(
                        tenant_id=DEFAULT_TENANT,
                        customer_id="cust_456",
                        status="shipped",
                        ship_date="2025-06-05",
                        delivery_date="2025-06-10",
                        total=4590.0,
                    ),
                    Order(
                        tenant_id=DEFAULT_TENANT,
                        customer_id="cust_456",
                        status="processing",
                        ship_date=None,
                        delivery_date=None,
                        total=1290.0,
                    ),
                    Order(
                        tenant_id=DEFAULT_TENANT,
                        customer_id="cust_789",
                        status="delivered",
                        ship_date="2025-05-20",
                        delivery_date="2025-05-25",
                        total=890.0,
                    ),
                    Order(
                        tenant_id="acme",
                        customer_id="cust_acme",
                        status="shipped",
                        ship_date="2025-06-01",
                        delivery_date="2025-06-06",
                        total=9900.0,
                    ),
                ]
            )
            db.add_all(
                [
                    Invoice(
                        tenant_id=DEFAULT_TENANT,
                        customer_id="cust_456",
                        order_id=1,
                        amount=4590.0,
                        status="paid",
                        due_date="2025-06-01",
                    ),
                    Invoice(
                        tenant_id=DEFAULT_TENANT,
                        customer_id="cust_456",
                        order_id=2,
                        amount=1290.0,
                        status="pending",
                        due_date="2025-06-15",
                    ),
                    Invoice(
                        tenant_id=DEFAULT_TENANT,
                        customer_id="cust_789",
                        order_id=3,
                        amount=890.0,
                        status="paid",
                        due_date="2025-05-18",
                    ),
                    Invoice(
                        tenant_id="acme",
                        customer_id="cust_acme",
                        order_id=4,
                        amount=9900.0,
                        status="paid",
                        due_date="2025-06-01",
                    ),
                ]
            )
            db.commit()


def get_db() -> Session:
    return SessionLocal()


def get_session(session_id: str, *, tenant_id: str = DEFAULT_TENANT) -> dict | None:
    with SessionLocal() as db:
        row = (
            db.query(ChatSession)
            .filter(
                ChatSession.session_id == session_id,
                ChatSession.tenant_id == tenant_id,
            )
            .first()
        )
        if not row:
            return None
        return {
            "session_id": row.session_id,
            "tenant_id": row.tenant_id,
            "customer_id": row.customer_id,
            "summary": row.summary or "",
            "messages": row.messages or [],
            "status": row.status,
            "ticket_id": row.ticket_id,
        }


def delete_session(session_id: str, *, tenant_id: str = DEFAULT_TENANT) -> None:
    with SessionLocal() as db:
        db.query(Feedback).filter(
            Feedback.session_id == session_id,
            Feedback.tenant_id == tenant_id,
        ).delete()
        row = (
            db.query(ChatSession)
            .filter(
                ChatSession.session_id == session_id,
                ChatSession.tenant_id == tenant_id,
            )
            .first()
        )
        if row:
            db.delete(row)
        db.commit()


def get_order_status(
    order_id: int,
    customer_id: str | None,
    *,
    tenant_id: str = DEFAULT_TENANT,
) -> dict | None:
    cached = get_cached_order(order_id, customer_id, tenant_id)
    if cached is not None:
        return cached

    with SessionLocal() as db:
        query = db.query(Order).filter(
            Order.order_id == order_id,
            Order.tenant_id == tenant_id,
        )
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        row = query.first()
        if not row:
            return None
        data = {
            "order_id": row.order_id,
            "tenant_id": row.tenant_id,
            "customer_id": row.customer_id,
            "status": row.status,
            "ship_date": row.ship_date,
            "delivery_date": row.delivery_date,
            "total": row.total,
        }
        set_cached_order(order_id, customer_id, data, tenant_id)
        return data


def get_account_info(customer_id: str, *, tenant_id: str = DEFAULT_TENANT) -> dict | None:
    with SessionLocal() as db:
        row = (
            db.query(Customer)
            .filter(
                Customer.customer_id == customer_id,
                Customer.tenant_id == tenant_id,
            )
            .first()
        )
        if not row:
            return None
        return {
            "tenant_id": row.tenant_id,
            "customer_id": row.customer_id,
            "name": row.name,
            "email": row.email,
            "plan": row.plan,
            "balance": row.balance,
        }


def list_customer_orders(customer_id: str, *, tenant_id: str = DEFAULT_TENANT) -> list[dict]:
    cached = get_cached_orders_list(customer_id, tenant_id)
    if cached is not None:
        return cached

    with SessionLocal() as db:
        rows = (
            db.query(Order)
            .filter(
                Order.customer_id == customer_id,
                Order.tenant_id == tenant_id,
            )
            .all()
        )
        data = [
            {
                "order_id": r.order_id,
                "status": r.status,
                "ship_date": r.ship_date,
                "delivery_date": r.delivery_date,
                "total": r.total,
            }
            for r in rows
        ]
    set_cached_orders_list(customer_id, data, tenant_id)
    return data


def list_customer_invoices(customer_id: str, *, tenant_id: str = DEFAULT_TENANT) -> list[dict]:
    with SessionLocal() as db:
        rows = (
            db.query(Invoice)
            .filter(
                Invoice.customer_id == customer_id,
                Invoice.tenant_id == tenant_id,
            )
            .all()
        )
        return [
            {
                "invoice_id": r.invoice_id,
                "order_id": r.order_id,
                "amount": r.amount,
                "status": r.status,
                "due_date": r.due_date,
            }
            for r in rows
        ]


def save_feedback(
    session_id: str,
    rating: int,
    customer_id: str | None = None,
    comment: str | None = None,
    *,
    tenant_id: str = DEFAULT_TENANT,
) -> dict:
    with SessionLocal() as db:
        row = Feedback(
            tenant_id=tenant_id,
            session_id=session_id,
            customer_id=customer_id,
            rating=rating,
            comment=comment,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {
            "feedback_id": row.feedback_id,
            "session_id": row.session_id,
            "rating": row.rating,
        }


def list_feedback_for_session(session_id: str, *, tenant_id: str = DEFAULT_TENANT) -> list[dict]:
    with SessionLocal() as db:
        rows = (
            db.query(Feedback)
            .filter(
                Feedback.session_id == session_id,
                Feedback.tenant_id == tenant_id,
            )
            .all()
        )
        return [
            {
                "feedback_id": r.feedback_id,
                "session_id": r.session_id,
                "customer_id": r.customer_id,
                "rating": r.rating,
                "comment": r.comment,
            }
            for r in rows
        ]


def list_feedback(limit: int = 50, *, tenant_id: str | None = None) -> list[dict]:
    with SessionLocal() as db:
        query = db.query(Feedback)
        if tenant_id:
            query = query.filter(Feedback.tenant_id == tenant_id)
        rows = query.order_by(Feedback.created_at.desc()).limit(limit).all()
        return [
            {
                "feedback_id": r.feedback_id,
                "tenant_id": r.tenant_id,
                "session_id": r.session_id,
                "customer_id": r.customer_id,
                "rating": r.rating,
                "comment": r.comment,
            }
            for r in rows
        ]


def list_sessions(
    status: str | None = None,
    limit: int = 50,
    *,
    tenant_id: str | None = None,
) -> list[dict]:
    with SessionLocal() as db:
        query = db.query(ChatSession)
        if tenant_id:
            query = query.filter(ChatSession.tenant_id == tenant_id)
        if status:
            query = query.filter(ChatSession.status == status)
        rows = query.order_by(ChatSession.updated_at.desc()).limit(limit).all()
        return [
            {
                "session_id": r.session_id,
                "tenant_id": r.tenant_id,
                "customer_id": r.customer_id,
                "status": r.status,
                "summary": r.summary,
                "ticket_id": r.ticket_id,
                "message_count": len(r.messages or []),
            }
            for r in rows
        ]


def get_analytics_stats(*, tenant_id: str | None = None) -> dict:
    with SessionLocal() as db:
        session_query = db.query(ChatSession)
        feedback_query = db.query(Feedback)
        if tenant_id:
            session_query = session_query.filter(ChatSession.tenant_id == tenant_id)
            feedback_query = feedback_query.filter(Feedback.tenant_id == tenant_id)
        total_sessions = session_query.count()
        awaiting = session_query.filter(ChatSession.status == "awaiting_operator").count()
        closed = session_query.filter(ChatSession.status == "closed").count()
        feedback_rows = feedback_query.all()
        avg_rating = None
        if feedback_rows:
            avg_rating = round(sum(r.rating for r in feedback_rows) / len(feedback_rows), 2)
        return {
            "sessions_total": total_sessions,
            "sessions_awaiting_operator": awaiting,
            "sessions_closed": closed,
            "feedback_count": len(feedback_rows),
            "feedback_avg_rating": avg_rating,
        }
