"""Pytest configuration and shared fixtures for the Aegis AI test suite.

All fixtures use pytest-asyncio with asyncio_mode = "auto" (configured in
pyproject.toml), so async fixtures and test functions work without decorators.
"""

from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.infrastructure.database.connection import get_db
from aegis.main import app


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """A mock AsyncSession that succeeds on all basic operations."""
    session = AsyncMock(spec=AsyncSession)
    # execute() returns a mock result that won't raise
    session.execute = AsyncMock(return_value=MagicMock())
    session.close = AsyncMock()
    return session


@pytest.fixture
def override_db(mock_db_session: AsyncMock) -> Generator[None, None, None]:
    """Override the get_db FastAPI dependency for the duration of a test."""

    async def _mock_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_db_session

    app.dependency_overrides[get_db] = _mock_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_db: None) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client pointed at the FastAPI app via ASGI transport.

    Uses the override_db fixture so no real database connection is required.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
