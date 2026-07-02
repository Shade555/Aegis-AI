"""Registry for mapping agent names to their concrete classes.

Allows dynamic instantiation of agents based on WorkItem definitions.
"""

from collections.abc import Callable

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.ports import EventBus, Logger


class AgentNotFoundError(Exception):
    """Raised when an unregistered agent name is requested."""


class WorkItemRegistry:
    """Registry that maps agent string names to their factory functions."""

    def __init__(self) -> None:
        self._registry: dict[str, Callable[[EventBus, Logger], BaseAgent]] = {}

    def register(self, agent_name: str, factory: Callable[[EventBus, Logger], BaseAgent]) -> None:
        """Register a new agent factory under a specific name.

        Args:
            agent_name: Unique string identifying the agent.
            factory: Callable that takes EventBus and Logger, returning a BaseAgent.
        """
        if agent_name in self._registry:
            raise ValueError(f"Agent '{agent_name}' is already registered.")
        self._registry[agent_name] = factory

    def get_agent(self, agent_name: str, event_bus: EventBus, logger: Logger) -> BaseAgent:
        """Instantiate and return the requested agent.

        Args:
            agent_name: Name of the agent to instantiate.
            event_bus: The EventBus instance to inject.
            logger: The Logger instance to inject.

        Returns:
            An instantiated BaseAgent subclass.

        Raises:
            AgentNotFoundError: If the agent name is not registered.
        """
        factory = self._registry.get(agent_name)
        if not factory:
            raise AgentNotFoundError(f"No agent registered with name '{agent_name}'.")

        return factory(event_bus, logger)
