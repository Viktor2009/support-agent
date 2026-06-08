import asyncio

from app.async_database import ping_database_async, reset_async_engine
from app.config import to_async_database_url, to_psycopg_conninfo, to_sync_database_url


def test_to_async_database_url_sqlite():
    assert (
        to_async_database_url("sqlite:///./support.db")
        == "sqlite+aiosqlite:///./support.db"
    )


def test_to_sync_database_url_postgres():
    assert (
        to_sync_database_url("postgresql://user:pass@localhost/db")
        == "postgresql+psycopg://user:pass@localhost/db"
    )


def test_to_psycopg_conninfo():
    assert (
        to_psycopg_conninfo("postgresql://user:pass@localhost/db")
        == "postgresql://user:pass@localhost/db"
    )


def test_to_async_database_url_postgres():
    assert (
        to_async_database_url("postgresql://user:pass@localhost/db")
        == "postgresql+asyncpg://user:pass@localhost/db"
    )


def test_ping_database_async(isolated_env):
    reset_async_engine()
    assert asyncio.run(ping_database_async()) == "ok"
