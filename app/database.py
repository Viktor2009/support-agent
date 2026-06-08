from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    plan = Column(String, nullable=False)
    balance = Column(Float, default=0.0)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    ship_date = Column(String, nullable=True)
    delivery_date = Column(String, nullable=True)
    total = Column(Float, nullable=False)


class ChatSession(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=True)
    summary = Column(Text, default="")
    messages = Column(JSON, default=list)
    status = Column(String, default="active")
    ticket_id = Column(String, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


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
                        customer_id="cust_456",
                        name="Иван Петров",
                        email="ivan@example.com",
                        plan="pro",
                        balance=1200.0,
                    ),
                    Customer(
                        customer_id="cust_789",
                        name="Мария Сидорова",
                        email="maria@example.com",
                        plan="basic",
                        balance=0.0,
                    ),
                ]
            )
            db.add_all(
                [
                    Order(
                        customer_id="cust_456",
                        status="shipped",
                        ship_date="2025-06-05",
                        delivery_date="2025-06-10",
                        total=4590.0,
                    ),
                    Order(
                        customer_id="cust_456",
                        status="processing",
                        ship_date=None,
                        delivery_date=None,
                        total=1290.0,
                    ),
                    Order(
                        customer_id="cust_789",
                        status="delivered",
                        ship_date="2025-05-20",
                        delivery_date="2025-05-25",
                        total=890.0,
                    ),
                ]
            )
            db.commit()


def get_db() -> Session:
    return SessionLocal()


def get_order_status(order_id: int, customer_id: str | None) -> dict | None:
    with SessionLocal() as db:
        query = db.query(Order).filter(Order.order_id == order_id)
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        row = query.first()
        if not row:
            return None
        return {
            "order_id": row.order_id,
            "customer_id": row.customer_id,
            "status": row.status,
            "ship_date": row.ship_date,
            "delivery_date": row.delivery_date,
            "total": row.total,
        }


def get_account_info(customer_id: str) -> dict | None:
    with SessionLocal() as db:
        row = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not row:
            return None
        return {
            "customer_id": row.customer_id,
            "name": row.name,
            "email": row.email,
            "plan": row.plan,
            "balance": row.balance,
        }


def list_customer_orders(customer_id: str) -> list[dict]:
    with SessionLocal() as db:
        rows = db.query(Order).filter(Order.customer_id == customer_id).all()
        return [
            {
                "order_id": r.order_id,
                "status": r.status,
                "ship_date": r.ship_date,
                "delivery_date": r.delivery_date,
                "total": r.total,
            }
            for r in rows
        ]
