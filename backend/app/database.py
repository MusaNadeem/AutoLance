"""
AutoLance — Database Engine & Session Management
SQLAlchemy 2.0 async with pgvector support
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


# ── SQLAlchemy Async Engine ──────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=settings.DEBUG,
)

# ── Session Factory ──────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── Base Model ───────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency Injection ─────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for use outside the request lifecycle (Celery workers, tasks).

    Celery tasks each call ``asyncio.run()`` which spins up a fresh event loop
    and closes it when the coroutine finishes. The module-level async ``engine``
    can retain asyncpg connection state bound to a previous loop, which makes the
    NEXT task fail with ``MissingGreenlet``. Disposing the engine at the end of
    every worker DB session guarantees no loop-bound resources survive into the
    next task's event loop. (NullPool makes this cheap — no pool to tear down.)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    # Release any loop-bound engine resources before this event loop closes.
    await engine.dispose()


async def create_tables():
    """Create all tables — used in development. Use Alembic for production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all tables — development only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
