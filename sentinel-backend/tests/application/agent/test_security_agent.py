"""Unit tests for the SecurityAnalysisAgent."""

import uuid
from pathlib import Path
from typing import Any

import pytest

from aegis.application.agent.models import AgentContext, AgentState
from aegis.application.agent.repository import RepositoryManifest
from aegis.application.agent.security import SecurityAnalysisAgent
from aegis.domain.events import AgentEventType


class MockEventBus:
    def __init__(self) -> None:
        self.events: list[tuple[AgentEventType, str, dict[str, Any]]] = []

    async def publish(self, event: Any) -> None:
        self.events.append((event.event_type, event.message, event.payload))


class MockLogger:
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        pass


@pytest.mark.asyncio
async def test_security_analysis_agent_success(tmp_path: Path) -> None:
    event_bus = MockEventBus()
    # Provide our mock rules so we don't rely on the filesystem or real rules failing
    from tests.application.security.test_security_engine import DummyRule

    agent = SecurityAnalysisAgent("security_1", event_bus, MockLogger(), rules=[DummyRule()])

    # Construct a manifest
    manifest = RepositoryManifest(
        project_type="Python",
        languages_used={"python": 1},
    )

    context = AgentContext(
        audit_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        agent_run_id=uuid.uuid4(),
        shared_state={
            "repository_manifest": manifest.model_dump(mode="json"),
            "repo_path": str(tmp_path),
        },
    )

    result = await agent.execute(context)

    assert result.status == AgentState.COMPLETE
    assert result.metadata["total_findings"] == 1

    # Verify events
    event_types = [e[0] for e in event_bus.events]
    assert AgentEventType.SECURITY_SCAN_STARTED in event_types
    assert AgentEventType.RULE_STARTED in event_types
    assert AgentEventType.FINDING_DETECTED in event_types
    assert AgentEventType.RULE_COMPLETED in event_types
    assert AgentEventType.SECURITY_SCAN_COMPLETED in event_types


@pytest.mark.asyncio
async def test_security_analysis_agent_missing_manifest() -> None:
    event_bus = MockEventBus()
    agent = SecurityAnalysisAgent("security_1", event_bus, MockLogger())

    context = AgentContext(
        audit_id=uuid.uuid4(), project_id=uuid.uuid4(), agent_run_id=uuid.uuid4(), shared_state={}
    )

    result = await agent.execute(context)

    assert result.status == AgentState.FAILED
    assert result.metadata["error"] == "Missing repository_manifest or repo_path"
