from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings, to_async_database_url

async_engine = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def _async_engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite+aiosqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


def reset_async_engine(url: str | None = None) -> None:
    """Create or recreate async engine (tests call with explicit URL)."""
    global async_engine, AsyncSessionLocal
    async_engine = None
    AsyncSessionLocal = None
    db_url = to_async_database_url(url or settings.database_url)
    async_engine = create_async_engine(db_url, **_async_engine_kwargs(db_url))
    AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


def init_async_db() -> None:
    if async_engine is None:
        reset_async_engine()


async def dispose_async_db() -> None:
    global async_engine, AsyncSessionLocal
    if async_engine is not None:
        await async_engine.dispose()
    async_engine = None
    AsyncSessionLocal = None


async def ping_database_async() -> str:
    if AsyncSessionLocal is None:
        return "not_initialized"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"
