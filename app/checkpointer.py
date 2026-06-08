from langgraph.checkpoint.memory import MemorySaver

from app.config import is_postgres, settings

_checkpointer = None
_pool = None


def get_checkpointer():
    global _checkpointer, _pool
    if _checkpointer is None:
        if is_postgres():
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg_pool import ConnectionPool

            _pool = ConnectionPool(conninfo=settings.database_url, max_size=10, open=True)
            _checkpointer = PostgresSaver(_pool)
            _checkpointer.setup()
        else:
            _checkpointer = MemorySaver()
    return _checkpointer


def init_checkpointer() -> None:
    get_checkpointer()


def shutdown_checkpointer() -> None:
    global _checkpointer, _pool
    if _pool is not None:
        _pool.close()
    _checkpointer = None
    _pool = None


def reset_checkpointer() -> None:
    """Drop checkpointer (for test isolation)."""
    shutdown_checkpointer()
