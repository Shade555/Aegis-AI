"""Unit tests for the SupervisorAgent."""

import uuid

import pytest

from aegis.application.agent.models import AgentContext, AgentState
from aegis.application.agent.supervisor import SupervisorAgent
from aegis.domain.events import AgentEventType
from tests.application.agent.test_framework import MockEventBus, MockLogger


@pytest.mark.asyncio
async def test_supervisor_agent_execution_plan() -> None:
    """The Supervisor should analyze context and generate an execution plan."""
    logger = MockLogger()
    event_bus = MockEventBus()
    supervisor = SupervisorAgent(name="supervisor", event_bus=event_bus, logger=logger)

    context = AgentContext(
        audit_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        agent_run_id=uuid.uuid4(),
    )

    result = await supervisor.run(context)

    # 1. Check result
    assert result.status == AgentState.COMPLETE
    assert result.metadata.get("plan_generated") is True
    assert result.metadata.get("tasks") == 3

    # 2. Check that the plan was mutated into shared_state
    assert "execution_plan" in context.shared_state
    plan = context.shared_state["execution_plan"]
    assert isinstance(plan, dict)
    assert len(plan["tasks"]) == 3

    # Check that tasks match expected mocked values
    tasks = plan["tasks"]
    assert tasks[0]["agent_name"] == "repository_agent"
    assert tasks[0]["dependencies"] == []

    assert tasks[1]["agent_name"] == "security_agent"
    assert tasks[1]["dependencies"] == ["repository_agent"]

    # 3. Check emitted events
    # Expected order: STARTED -> PROGRESS -> PROGRESS -> COMPLETE
    assert len(event_bus.events) == 4

    assert event_bus.events[0].event_type == AgentEventType.STARTED

    assert event_bus.events[1].event_type == AgentEventType.PROGRESS
    assert "Analyzing repository context" in event_bus.events[1].message

    assert event_bus.events[2].event_type == AgentEventType.PROGRESS
    assert "Execution plan formulated successfully" in event_bus.events[2].message
    assert event_bus.events[2].payload.get("task_count") == 3

    assert event_bus.events[3].event_type == AgentEventType.COMPLETE
