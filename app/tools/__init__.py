from app.database import (
    get_account_info,
    get_order_status,
    list_customer_invoices,
    list_customer_orders,
)
from app.tools.registry import register_tool


def bootstrap_tools() -> None:
    register_tool("get_order_status", get_order_status)
    register_tool("list_customer_orders", list_customer_orders)
    register_tool("list_customer_invoices", list_customer_invoices)
    register_tool("get_account_info", get_account_info)
