"""Tests for Executions Router."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from aegis.main import app


@pytest.mark.asyncio
async def test_get_execution_status_not_found() -> None:
    exec_id = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/executions/{exec_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "AnalysisNotFoundError"


@pytest.mark.asyncio
async def test_get_execution_findings_not_found() -> None:
    exec_id = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/executions/{exec_id}/findings")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_execution_manifest_not_found() -> None:
    exec_id = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/executions/{exec_id}/manifest")

    assert response.status_code == 404
