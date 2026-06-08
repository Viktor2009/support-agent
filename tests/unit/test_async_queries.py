import asyncio

from app.async_queries import aget_order_status, alist_customer_orders
from app.async_session_store import aload_session, asave_session


def test_async_order_status():
    data = asyncio.run(aget_order_status(1, "cust_456", tenant_id="default"))
    assert data is not None
    assert data["status"] == "shipped"


def test_async_list_orders():
    orders = asyncio.run(alist_customer_orders("cust_456", tenant_id="default"))
    assert len(orders) >= 1


def test_async_session_roundtrip():
    asyncio.run(
        asave_session(
            "async-s1",
            "cust_456",
            "summary test",
            [{"role": "user", "content": "hi"}],
            tenant_id="default",
        )
    )
    stored = asyncio.run(aload_session("async-s1", tenant_id="default"))
    assert stored["customer_id"] == "cust_456"
    assert stored["summary"] == "summary test"
    assert stored["messages"][0]["content"] == "hi"
