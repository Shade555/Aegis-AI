"""Abstract base class for all AI agents in the Aegis framework.

Implements the Template Method pattern to enforce a standard execution lifecycle,
including automatic event emission and error handling, while deferring the
actual business logic to subclasses.
"""

import traceback
from abc import ABC, abstractmethod
from typing import Any

from aegis.application.agent.models import AgentContext, AgentResult, AgentState
from aegis.application.agent.ports import EventBus, Logger
from aegis.domain.events import AgentEvent, AgentEventType


class BaseAgent(ABC):
    """Abstract base class representing an autonomous agent.

    All agents must inherit from this class and implement the `execute` method.
    The lifecycle is managed by the `run` method, which guarantees that events
    are emitted appropriately regardless of success or failure.
    """

    def __init__(self, name: str, event_bus: EventBus, logger: Logger) -> None:
        """Initialize the agent with its name and injected dependencies."""
        self.name = name
        self.event_bus = event_bus
        self.logger = logger

    async def _emit_event(
        self,
        context: AgentContext,
        event_type: AgentEventType,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Helper to emit an event using the injected EventBus."""
        event = AgentEvent(
            audit_id=context.audit_id,
            agent_run_id=context.agent_run_id,
            agent_name=self.name,
            event_type=event_type,
            message=message,
            payload=payload or {},
        )
        try:
            await self.event_bus.publish(event)
        except Exception as exc:
            # We log but do not raise, so event bus failures don't crash the agent logic.
            self.logger.error(f"Failed to publish event {event_type}: {exc}")

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """The core business logic of the agent. Must be implemented by subclasses.

        Args:
            context: The execution context containing necessary IDs and shared state.

        Returns:
            An AgentResult detailing the outcome.
        """
        ...

    async def run(self, context: AgentContext) -> AgentResult:
        """Template method that manages the execution lifecycle of the agent.

        Emits STARTED and COMPLETE/ERROR events automatically.
        Wraps the subclass's execute() method in a safe try-except block.
        """
        self.logger.info(f"Agent {self.name} starting execution for audit {context.audit_id}")
        await self._emit_event(
            context=context,
            event_type=AgentEventType.STARTED,
            message=f"Agent {self.name} started.",
        )

        try:
            result = await self.execute(context)

            await self._emit_event(
                context=context,
                event_type=AgentEventType.COMPLETE,
                message=f"Agent {self.name} completed successfully.",
                payload={"result_status": result.status.value, "metadata": result.metadata},
            )
            return result

        except Exception as exc:
            error_msg = str(exc)
            stack_trace = traceback.format_exc()
            self.logger.error(f"Agent {self.name} failed: {error_msg}\n{stack_trace}")

            await self._emit_event(
                context=context,
                event_type=AgentEventType.ERROR,
                message=f"Agent {self.name} encountered a critical error: {error_msg}",
                payload={"traceback": stack_trace},
            )
            return AgentResult(
                status=AgentState.FAILED,
                confidence=0.0,
                error_message=error_msg,
            )
