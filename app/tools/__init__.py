from app.async_queries import (
    aget_account_info,
    aget_order_status,
    alist_customer_invoices,
    alist_customer_orders,
)
from app.tools.registry import register_tool


def bootstrap_tools() -> None:
    register_tool("get_order_status", aget_order_status)
    register_tool("list_customer_orders", alist_customer_orders)
    register_tool("list_customer_invoices", alist_customer_invoices)
    register_tool("get_account_info", aget_account_info)
