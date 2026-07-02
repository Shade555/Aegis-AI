"""Tests for AnalysisService."""

import uuid
from pathlib import Path

import pytest
from fastapi import BackgroundTasks

from aegis.application.execution.manager import SessionManager
from aegis.application.services.analysis import AnalysisService


@pytest.fixture
def session_manager() -> SessionManager:
    return SessionManager()


@pytest.fixture
def analysis_service(session_manager: SessionManager) -> AnalysisService:
    return AnalysisService(session_manager)


@pytest.mark.asyncio
async def test_start_analysis_local_path(analysis_service: AnalysisService, tmp_path: Path) -> None:
    background_tasks = BackgroundTasks()

    execution_id = await analysis_service.start_analysis(
        project_path=str(tmp_path), upload_file=None, background_tasks=background_tasks
    )

    assert execution_id is not None
    session = analysis_service.get_execution(execution_id)
    assert session is not None
    assert session.execution_id == execution_id


@pytest.mark.asyncio
async def test_start_analysis_invalid_local_path(
    analysis_service: AnalysisService,
) -> None:
    background_tasks = BackgroundTasks()

    with pytest.raises(ValueError):
        await analysis_service.start_analysis(
            project_path="/does/not/exist", upload_file=None, background_tasks=background_tasks
        )


def test_get_findings_empty(analysis_service: AnalysisService) -> None:
    execution_id = uuid.uuid4()
    findings = analysis_service.get_findings(execution_id)
    assert findings is None
