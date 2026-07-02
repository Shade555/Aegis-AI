"""Tests for Projects Router."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.main import app


@pytest.mark.asyncio
async def test_analyze_project_missing_path() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/projects/analyze")

    # Validation error or InvalidProjectStateError
    assert response.status_code == 400
    assert "Must provide either local_path, demo_id, or an uploaded file" in response.text


@pytest.mark.asyncio
async def test_analyze_project_valid_path(tmp_path: Path) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/projects/analyze", data={"local_path": str(tmp_path)})

    assert response.status_code == 200
    data = response.json()
    assert "execution_id" in data
    assert data["status"] == "PENDING"
