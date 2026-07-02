"""Health endpoint tests."""

from httpx import AsyncClient


async def test_health_returns_200(client: AsyncClient) -> None:
    """Health endpoint returns HTTP 200."""
    response = await client.get("/health")
    assert response.status_code == 200


async def test_health_response_contains_required_fields(client: AsyncClient) -> None:
    """Response body includes all required top-level fields."""
    response = await client.get("/health")
    body = response.json()
    assert "status" in body
    assert "version" in body
    assert "env" in body
    assert "uptime_seconds" in body
    assert body["status"] == "ok"


async def test_health_returns_correct_version(client: AsyncClient) -> None:
    """Version field matches the application version from settings."""
    from aegis.config import settings

    response = await client.get("/health")
    body = response.json()
    assert body["version"] == settings.app_version
