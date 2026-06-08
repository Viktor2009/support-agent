import inspect
from collections.abc import Callable
from typing import Any

ToolFn = Callable[..., Any]

_REGISTRY: dict[str, ToolFn] = {}


def register_tool(name: str, fn: ToolFn) -> None:
    _REGISTRY[name] = fn


def get_tool(name: str) -> ToolFn | None:
    return _REGISTRY.get(name)


def list_tools() -> list[str]:
    return sorted(_REGISTRY.keys())


def run_tool(name: str, **kwargs: Any) -> Any:
    tool = get_tool(name)
    if tool is None:
        raise KeyError(f"Tool '{name}' is not registered")
    return tool(**kwargs)


async def arun_tool(name: str, **kwargs: Any) -> Any:
    tool = get_tool(name)
    if tool is None:
        raise KeyError(f"Tool '{name}' is not registered")
    result = tool(**kwargs)
    if inspect.isawaitable(result):
        return await result
    return result
