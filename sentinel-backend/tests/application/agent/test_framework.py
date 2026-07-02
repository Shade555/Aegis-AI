"""Unit tests for the core Agent Framework abstractions."""

import uuid

import pytest
from pydantic import ValidationError

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.models import AgentContext, AgentResult, AgentState, WorkItem
from aegis.application.agent.ports import EventBus, Logger
from aegis.application.agent.registry import AgentNotFoundError, WorkItemRegistry
from aegis.domain.events import AgentEvent, AgentEventType

# ── Mocks ────────────────────────────────────────────────────────────────────


class MockLogger(Logger):
    def __init__(self) -> None:
        self.logs: list[tuple[str, str]] = []

    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logs.append(("info", msg))

    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logs.append(("error", msg))

    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logs.append(("warning", msg))

    def debug(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logs.append(("debug", msg))


class MockEventBus(EventBus):
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []
        self.should_fail = False

    async def publish(self, event: AgentEvent) -> None:
        if self.should_fail:
            raise RuntimeError("Event bus failure")
        self.events.append(event)


# ── Dummy Agents ─────────────────────────────────────────────────────────────


class DummySuccessAgent(BaseAgent):
    """An agent that always succeeds."""

    async def execute(self, context: AgentContext) -> AgentResult:
        # Emit a custom PROGRESS event
        await self._emit_event(context, AgentEventType.PROGRESS, "Doing work...")
        return AgentResult(status=AgentState.COMPLETE, confidence=0.9, metadata={"found": 42})


class DummyFailingAgent(BaseAgent):
    """An agent that raises an exception during execution."""

    async def execute(self, context: AgentContext) -> AgentResult:
        raise ValueError("Simulated catastrophic failure")


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_success_lifecycle() -> None:
    """A successful agent run emits STARTED, custom PROGRESS, and COMPLETE events."""
    logger = MockLogger()
    event_bus = MockEventBus()
    agent = DummySuccessAgent(name="success_agent", event_bus=event_bus, logger=logger)

    context = AgentContext(
        audit_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        agent_run_id=uuid.uuid4(),
    )

    result = await agent.run(context)

    # Check result
    assert result.status == AgentState.COMPLETE
    assert result.confidence == 0.9
    assert result.metadata == {"found": 42}

    # Check events (STARTED -> PROGRESS -> COMPLETE)
    assert len(event_bus.events) == 3
    assert event_bus.events[0].event_type == AgentEventType.STARTED
    assert event_bus.events[1].event_type == AgentEventType.PROGRESS
    assert event_bus.events[1].message == "Doing work..."
    assert event_bus.events[2].event_type == AgentEventType.COMPLETE

    # Ensure all events have correct routing IDs
    for event in event_bus.events:
        assert event.audit_id == context.audit_id
        assert event.agent_run_id == context.agent_run_id
        assert event.agent_name == "success_agent"

    # Check logs
    assert any("starting execution" in msg for level, msg in logger.logs if level == "info")


@pytest.mark.asyncio
async def test_agent_error_lifecycle() -> None:
    """An agent that raises an exception emits an ERROR event and returns FAILED state."""
    logger = MockLogger()
    event_bus = MockEventBus()
    agent = DummyFailingAgent(name="failing_agent", event_bus=event_bus, logger=logger)

    context = AgentContext(
        audit_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        agent_run_id=uuid.uuid4(),
    )

    result = await agent.run(context)

    # Check result (should be FAILED, not raise)
    assert result.status == AgentState.FAILED
    assert result.error_message is not None
    assert "Simulated catastrophic failure" in result.error_message
    assert result.confidence == 0.0

    # Check events (STARTED -> ERROR)
    assert len(event_bus.events) == 2
    assert event_bus.events[0].event_type == AgentEventType.STARTED
    assert event_bus.events[1].event_type == AgentEventType.ERROR
    assert "Simulated catastrophic failure" in event_bus.events[1].message
    assert "traceback" in event_bus.events[1].payload

    # Check logs
    assert any(
        "Simulated catastrophic failure" in msg for level, msg in logger.logs if level == "error"
    )


@pytest.mark.asyncio
async def test_agent_event_bus_failure_does_not_crash_agent() -> None:
    """If the EventBus throws an exception, the agent logs it but continues execution."""
    logger = MockLogger()
    event_bus = MockEventBus()
    event_bus.should_fail = True  # Force publish() to raise RuntimeError

    agent = DummySuccessAgent(name="resilient_agent", event_bus=event_bus, logger=logger)
    context = AgentContext(
        audit_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        agent_run_id=uuid.uuid4(),
    )

    result = await agent.run(context)

    # Execution still completes successfully
    assert result.status == AgentState.COMPLETE

    # Events were not recorded due to failure
    assert len(event_bus.events) == 0

    # Errors were logged
    assert any("Failed to publish event" in msg for level, msg in logger.logs if level == "error")


def test_work_item_registry() -> None:
    """Test registering and resolving agents via WorkItemRegistry."""
    registry = WorkItemRegistry()

    # Register factory
    def factory(eb: EventBus, lg: Logger) -> BaseAgent:
        return DummySuccessAgent("dummy", eb, lg)

    registry.register("dummy", factory)

    # Resolve
    agent = registry.get_agent("dummy", MockEventBus(), MockLogger())
    assert isinstance(agent, DummySuccessAgent)
    assert agent.name == "dummy"

    # Duplicate registration raises ValueError
    with pytest.raises(ValueError, match="already registered"):
        registry.register("dummy", factory)

    # Unregistered name raises AgentNotFoundError
    with pytest.raises(AgentNotFoundError):
        registry.get_agent("unknown", MockEventBus(), MockLogger())


def test_pydantic_validation() -> None:
    """Ensure strict Pydantic validation is working on the pure models."""

    # AgentResult confidence must be between 0 and 1
    with pytest.raises(ValidationError):
        AgentResult(status=AgentState.COMPLETE, confidence=1.5)

    # WorkItem requires UUIDs
    with pytest.raises(ValidationError):
        WorkItem(
            audit_id="not-a-uuid",  # type: ignore
            project_id=uuid.uuid4(),
            agent_run_id=uuid.uuid4(),
            agent_name="test",
        )
