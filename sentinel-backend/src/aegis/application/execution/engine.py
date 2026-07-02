"""Execution engine that runs agents and manages session state."""

import traceback
import uuid
from typing import Any

from aegis.application.agent.models import AgentContext, AgentResult, AgentState
from aegis.application.agent.ports import EventBus, Logger
from aegis.application.agent.registry import WorkItemRegistry
from aegis.application.execution.manager import session_manager
from aegis.application.execution.models import ExecutionEvent, ExecutionSession, ExecutionStatus
from aegis.domain.events import AgentEvent, AgentEventType


class SessionEventBus(EventBus):
    """An event bus that directly mutates the ExecutionSession's event history.

    Satisfies MVP constraints to store events directly in the session.
    """

    def __init__(self, session: ExecutionSession) -> None:
        self.session = session

    async def publish(self, event: AgentEvent) -> None:
        """Converts the AgentEvent to an ExecutionEvent and stores it."""
        exec_event = ExecutionEvent(
            execution_id=self.session.execution_id,
            agent_id=event.agent_name,
            agent_run_id=event.agent_run_id,
            event_type=event.event_type,
            message=event.message,
            metadata=event.payload,
        )
        self.session.event_history.append(exec_event)
        session_manager.broadcast_event(self.session.audit_id, exec_event)

        if event.event_type == AgentEventType.COMPLETE:
            if event.payload and event.payload.get("result_status") == "FAILED":
                if event.agent_name not in self.session.failed_agents:
                    self.session.failed_agents.append(event.agent_name)
            else:
                if event.agent_name not in self.session.completed_agents:
                    self.session.completed_agents.append(event.agent_name)
            self.session.active_agent = None
        elif event.event_type == AgentEventType.ERROR:
            if event.agent_name not in self.session.failed_agents:
                self.session.failed_agents.append(event.agent_name)
            self.session.active_agent = None


class AgentExecutor:
    """Executes a chain of agents against a given ExecutionSession."""

    def __init__(self, registry: WorkItemRegistry, logger: Logger) -> None:
        self.registry = registry
        self.logger = logger

    async def run_session(
        self, session: ExecutionSession, agent_names: list[str], shared_state: dict[str, Any]
    ) -> None:
        """Executes a sequential list of agents."""

        try:
            session.transition_to(ExecutionStatus.RUNNING)
            event_bus = SessionEventBus(session)

            # Emit ExecutionStarted
            start_event = ExecutionEvent(
                execution_id=session.execution_id,
                event_type="ExecutionStarted",
                message="Execution session started",
            )
            session.event_history.append(start_event)
            session_manager.broadcast_event(session.audit_id, start_event)

            total_agents = len(agent_names)

            for index, agent_name in enumerate(agent_names):
                session.active_agent = agent_name

                # Setup context
                agent_run_id = uuid.uuid4()
                context = AgentContext(
                    audit_id=session.audit_id,
                    project_id=session.project_id,
                    agent_run_id=agent_run_id,
                    shared_state=shared_state,
                )

                # Fetch agent
                try:
                    agent = self.registry.get_agent(agent_name, event_bus, self.logger)
                except Exception as e:
                    self.logger.error(f"Failed to resolve agent {agent_name}: {e}")
                    session.failed_agents.append(agent_name)
                    session.transition_to(ExecutionStatus.FAILED)

                    failed_event = ExecutionEvent(
                        execution_id=session.execution_id,
                        event_type="ExecutionFailed",
                        message=f"Failed to resolve agent {agent_name}",
                    )
                    session.event_history.append(failed_event)
                    session_manager.broadcast_event(session.audit_id, failed_event)
                    return

                # Execute agent
                try:
                    result: AgentResult = await agent.run(context)

                    # Pydantic BaseModels deepcopy dicts, so we must propagate the mutated state back
                    shared_state.update(context.shared_state)

                    if result.status == AgentState.FAILED:
                        session.transition_to(ExecutionStatus.FAILED)

                        failed_event = ExecutionEvent(
                            execution_id=session.execution_id,
                            event_type="ExecutionFailed",
                            message=f"Agent {agent_name} failed",
                        )
                        session.event_history.append(failed_event)
                        session_manager.broadcast_event(session.audit_id, failed_event)
                        return
                except Exception as e:
                    self.logger.error(
                        f"Catastrophic failure in agent {agent_name}: {e}\n{traceback.format_exc()}"
                    )
                    session.failed_agents.append(agent_name)
                    session.transition_to(ExecutionStatus.FAILED)

                    failed_event = ExecutionEvent(
                        execution_id=session.execution_id,
                        event_type="ExecutionFailed",
                        message=f"Catastrophic failure in agent {agent_name}",
                    )
                    session.event_history.append(failed_event)
                    session_manager.broadcast_event(session.audit_id, failed_event)
                    return

                # Update progress
                session.progress_percentage = int(((index + 1) / total_agents) * 100)

            session.transition_to(ExecutionStatus.COMPLETED)
            complete_event = ExecutionEvent(
                execution_id=session.execution_id,
                event_type="ExecutionCompleted",
                message="Execution session completed successfully",
            )
            session.event_history.append(complete_event)
            session_manager.broadcast_event(session.audit_id, complete_event)

        except Exception as e:
            self.logger.error(f"Session execution failed: {e}")
            if session.current_state != ExecutionStatus.FAILED:
                session.transition_to(ExecutionStatus.FAILED)
            failed_event = ExecutionEvent(
                execution_id=session.execution_id,
                event_type="ExecutionFailed",
                message=f"Session execution failed: {e}",
            )
            session.event_history.append(failed_event)
            session_manager.broadcast_event(session.audit_id, failed_event)
