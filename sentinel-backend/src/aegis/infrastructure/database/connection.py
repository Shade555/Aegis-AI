"""Async SQLAlchemy engine, session factory, and FastAPI database dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from aegis.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models.

    All models import from here so Alembic autogenerate can discover them.
    """


# The engine is created once at module load time.
# pool_pre_ping ensures stale connections are recycled.
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.app_env == "development",
)

# Session factory — used to create individual request-scoped sessions.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a per-request async database session.

    The session is always closed in the finally block, regardless of whether
    the request succeeded or raised an exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
