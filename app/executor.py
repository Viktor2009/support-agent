from collections.abc import Callable
from functools import partial
from typing import TypeVar

from starlette.concurrency import run_in_threadpool

T = TypeVar("T")


async def run_sync(func: Callable[..., T], /, *args, **kwargs) -> T:
    """Run blocking graph/DB work off the event loop."""
    if kwargs:
        return await run_in_threadpool(partial(func, *args, **kwargs))
    if args:
        return await run_in_threadpool(partial(func, *args))
    return await run_in_threadpool(func)
