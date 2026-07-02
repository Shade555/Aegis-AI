"""Unit tests for the execution infrastructure."""

import uuid

import pytest

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.models import AgentContext, AgentResult, AgentState
from aegis.application.agent.ports import Logger
from aegis.application.agent.registry import WorkItemRegistry
from aegis.application.execution.engine import AgentExecutor
from aegis.application.execution.manager import session_manager
from aegis.application.execution.models import ExecutionSession, ExecutionStatus
from aegis.domain.events import AgentEventType


# Dummy Agents for testing
class SuccessAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        await self._emit_event(context, AgentEventType.PROGRESS, "Doing work...")
        return AgentResult(status=AgentState.COMPLETE, confidence=1.0)


class FailingAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        await self._emit_event(context, AgentEventType.ERROR, "I failed!")
        return AgentResult(status=AgentState.FAILED, error_message="I failed!")


class CrashAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        raise RuntimeError("Catastrophic boom")


class MockLogger(Logger):
    def debug(self, msg: str, *args: object, **kwargs: object) -> None:
        pass

    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        pass

    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        pass

    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        pass


@pytest.fixture
def registry() -> WorkItemRegistry:
    r = WorkItemRegistry()
    r.register("success", lambda eb, lg: SuccessAgent("success", eb, lg))
    r.register("success2", lambda eb, lg: SuccessAgent("success2", eb, lg))
    r.register("fail", lambda eb, lg: FailingAgent("fail", eb, lg))
    r.register("crash", lambda eb, lg: CrashAgent("crash", eb, lg))
    return r


@pytest.fixture
def executor(registry: WorkItemRegistry) -> AgentExecutor:
    return AgentExecutor(registry, MockLogger())


@pytest.fixture
def session() -> ExecutionSession:
    s = ExecutionSession(audit_id=uuid.uuid4(), project_id=uuid.uuid4())
    session_manager.register_session(s)
    return s


def test_session_manager(session: ExecutionSession) -> None:
    """Test session manager CRUD."""
    assert session_manager.get_session(session.audit_id) == session
    session_manager.remove_session(session.audit_id)
    assert session_manager.get_session(session.audit_id) is None


def test_invalid_state_transitions(session: ExecutionSession) -> None:
    """State machine prevents illegal transitions."""
    assert session.current_state.value == ExecutionStatus.CREATED.value

    # Valid
    session.transition_to(ExecutionStatus.QUEUED)
    assert session.current_state.value == ExecutionStatus.QUEUED.value

    # Invalid
    with pytest.raises(ValueError, match="Invalid transition"):
        session.transition_to(ExecutionStatus.CREATED)

    session.transition_to(ExecutionStatus.RUNNING)
    session.transition_to(ExecutionStatus.COMPLETED)

    # Invalid after complete
    with pytest.raises(ValueError, match="Invalid transition"):
        session.transition_to(ExecutionStatus.FAILED)


@pytest.mark.asyncio
async def test_successful_execution(executor: AgentExecutor, session: ExecutionSession) -> None:
    """Agents run sequentially and update progress/history."""
    await executor.run_session(session, ["success", "success2"], {})

    assert session.current_state == ExecutionStatus.COMPLETED
    assert session.progress_percentage == 100
    assert len(session.completed_agents) == 2
    assert not session.failed_agents

    # 2 agents * (STARTED, PROGRESS, COMPLETE) = 6 events + 2 execution events
    assert len(session.event_history) == 8
    assert session.event_history[1].event_type == AgentEventType.STARTED


@pytest.mark.asyncio
async def test_failing_execution(executor: AgentExecutor, session: ExecutionSession) -> None:
    """A failing agent stops the chain and marks session as failed."""
    await executor.run_session(session, ["success", "fail", "success"], {})

    assert session.current_state == ExecutionStatus.FAILED
    assert (
        session.progress_percentage == 33
    )  # It hit the second agent out of 3, but failed so progress is 1/3 completed
    assert len(session.completed_agents) == 1
    assert len(session.failed_agents) == 1

    # Check events
    # FailingAgent emits ERROR, then BaseAgent emits COMPLETE with FAILED status
    # Then AgentExecutor emits ExecutionFailed
    assert session.event_history[-3].event_type == AgentEventType.ERROR
    assert session.event_history[-2].event_type == AgentEventType.COMPLETE
    assert session.event_history[-2].metadata.get("result_status") == "FAILED"
    assert "I failed!" in session.event_history[-3].message
    assert session.event_history[-1].event_type == "ExecutionFailed"


@pytest.mark.asyncio
async def test_crashing_execution(executor: AgentExecutor, session: ExecutionSession) -> None:
    """An unhandled exception in an agent marks session as failed gracefully."""
    await executor.run_session(session, ["crash"], {})

    assert session.current_state == ExecutionStatus.FAILED
    assert "crash" in session.failed_agents
