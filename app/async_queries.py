from sqlalchemy import select

from app import async_database
from app.cached_db import (
    get_cached_order,
    get_cached_orders_list,
    set_cached_order,
    set_cached_orders_list,
)
from app.database import Customer, Invoice, Order
from app.tenant import DEFAULT_TENANT


def _session_factory():
    if async_database.AsyncSessionLocal is None:
        async_database.init_async_db()
    return async_database.AsyncSessionLocal


async def aget_order_status(
    order_id: int,
    customer_id: str | None,
    *,
    tenant_id: str = DEFAULT_TENANT,
) -> dict | None:
    cached = get_cached_order(order_id, customer_id, tenant_id)
    if cached is not None:
        return cached

    session_maker = _session_factory()
    async with session_maker() as session:
        stmt = select(Order).where(
            Order.order_id == order_id,
            Order.tenant_id == tenant_id,
        )
        if customer_id:
            stmt = stmt.where(Order.customer_id == customer_id)
        row = (await session.execute(stmt)).scalar_one_or_none()
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


async def aget_account_info(customer_id: str, *, tenant_id: str = DEFAULT_TENANT) -> dict | None:
    session_maker = _session_factory()
    async with session_maker() as session:
        row = (
            await session.execute(
                select(Customer).where(
                    Customer.customer_id == customer_id,
                    Customer.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
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


async def alist_customer_orders(customer_id: str, *, tenant_id: str = DEFAULT_TENANT) -> list[dict]:
    cached = get_cached_orders_list(customer_id, tenant_id)
    if cached is not None:
        return cached

    session_maker = _session_factory()
    async with session_maker() as session:
        rows = (
            await session.execute(
                select(Order).where(
                    Order.customer_id == customer_id,
                    Order.tenant_id == tenant_id,
                )
            )
        ).scalars().all()
        data = [
            {
                "order_id": row.order_id,
                "status": row.status,
                "ship_date": row.ship_date,
                "delivery_date": row.delivery_date,
                "total": row.total,
            }
            for row in rows
        ]
    set_cached_orders_list(customer_id, data, tenant_id)
    return data


async def alist_customer_invoices(customer_id: str, *, tenant_id: str = DEFAULT_TENANT) -> list[dict]:
    session_maker = _session_factory()
    async with session_maker() as session:
        rows = (
            await session.execute(
                select(Invoice).where(
                    Invoice.customer_id == customer_id,
                    Invoice.tenant_id == tenant_id,
                )
            )
        ).scalars().all()
        return [
            {
                "invoice_id": row.invoice_id,
                "order_id": row.order_id,
                "amount": row.amount,
                "status": row.status,
                "due_date": row.due_date,
            }
            for row in rows
        ]
