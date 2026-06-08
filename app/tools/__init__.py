import importlib

from app.async_queries import (
    aget_account_info,
    aget_order_status,
    alist_customer_invoices,
    alist_customer_orders,
)
from app.config import settings
from app.tools.registry import register_tool


def _load_plugin_tools() -> None:
    module_path = settings.plugin_module.strip()
    if not module_path:
        return
    module = importlib.import_module(module_path)
    register_fn = getattr(module, "register", None)
    if register_fn is None:
        raise RuntimeError(f"Plugin module '{module_path}' must expose register(register_tool)")
    register_fn(register_tool)


def bootstrap_tools() -> None:
    register_tool("get_order_status", aget_order_status)
    register_tool("list_customer_orders", alist_customer_orders)
    register_tool("list_customer_invoices", alist_customer_invoices)
    register_tool("get_account_info", aget_account_info)
    _load_plugin_tools()
