import asyncio

from langgraph.checkpoint.memory import MemorySaver

from app.config import is_postgres, settings, to_psycopg_conninfo

_checkpointer = None
_async_pool = None
_setup_done = False


async def init_checkpointer() -> None:
    global _checkpointer, _async_pool, _setup_done
    if _checkpointer is not None:
        return
    if is_postgres():
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool

        conninfo = to_psycopg_conninfo(settings.database_url)
        _async_pool = AsyncConnectionPool(conninfo=conninfo, max_size=10)
        await _async_pool.open()
        _checkpointer = AsyncPostgresSaver(_async_pool)
        if not _setup_done:
            await _checkpointer.setup()
            _setup_done = True
    else:
        _checkpointer = MemorySaver()


def get_checkpointer():
    global _checkpointer
    if _checkpointer is None:
        if is_postgres():
            raise RuntimeError(
                "Postgres checkpointer not initialized; call init_checkpointer() first"
            )
        _checkpointer = MemorySaver()
    return _checkpointer


async def shutdown_checkpointer() -> None:
    global _checkpointer, _async_pool, _setup_done
    if _async_pool is not None:
        await _async_pool.close()
    _checkpointer = None
    _async_pool = None
    _setup_done = False


def reset_checkpointer() -> None:
    """Drop checkpointer (for test isolation)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(shutdown_checkpointer())
        return
    global _checkpointer, _async_pool, _setup_done
    _checkpointer = None
    _async_pool = None
    _setup_done = False


async def ping_checkpointer() -> str:
    """Return checkpointer status for health checks."""
    try:
        if not is_postgres():
            if _checkpointer is None:
                await init_checkpointer()
            return "memory"
        if _checkpointer is None or _async_pool is None:
            return "not_initialized"
        async with _async_pool.connection() as conn:
            await conn.execute("SELECT 1")
        return "ok"
    except Exception:
        return "error"
