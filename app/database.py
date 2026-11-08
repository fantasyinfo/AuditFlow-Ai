import os
from collections.abc import AsyncGenerator, Generator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()


def normalize_async_database_url(url: str) -> str:
    """Normalize database connection string for asyncpg (used by FastAPI)."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    try:
        parsed = urlparse(url)
        query_params = dict(parse_qsl(parsed.query))
        # Remove parameters not accepted by asyncpg
        query_params.pop("channel_binding", None)
        # asyncpg prefers ssl= over sslmode=
        if "sslmode" in query_params:
            ssl_val = query_params.pop("sslmode")
            if "ssl" not in query_params:
                query_params["ssl"] = ssl_val

        new_query = urlencode(query_params)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url


def normalize_sync_database_url(url: str) -> str:
    """Normalize database connection string for psycopg2 (used by workers and migrations)."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


is_serverless = bool(os.environ.get("VERCEL"))
async_engine_kwargs = {"echo": False, "future": True}
sync_engine_kwargs = {"echo": False}

if is_serverless:
    async_engine_kwargs["poolclass"] = NullPool
    sync_engine_kwargs["poolclass"] = NullPool
else:
    async_engine_kwargs["pool_pre_ping"] = True
    sync_engine_kwargs["pool_pre_ping"] = True

# Asynchronous engine & session for FastAPI routes (asyncpg)
async_engine = create_async_engine(
    normalize_async_database_url(settings.DATABASE_URL),
    **async_engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Synchronous engine & session for Celery workers & migrations (psycopg2)
sync_engine = create_engine(
    normalize_sync_database_url(settings.SYNC_DATABASE_URL),
    **sync_engine_kwargs,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


get_async_db = get_db


def get_sync_db() -> Generator[Session, None, None]:
    """Synchronous context manager / generator yielding a sync database session for workers."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()

