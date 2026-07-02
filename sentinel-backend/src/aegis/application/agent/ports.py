"""Port definitions for external dependencies of the Agent Framework.

These Protocols ensure that the agent framework depends on abstractions,
not concrete implementations (Dependency Inversion Principle).
"""

from typing import Protocol

from aegis.domain.events import AgentEvent


class EventBus(Protocol):
    """Protocol for publishing domain events asynchronously."""

    async def publish(self, event: AgentEvent) -> None:
        """Publish an event to the underlying messaging system."""
        ...


class Logger(Protocol):
    """Protocol for structured logging within agents."""

    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log an informational message."""
        ...

    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log an error message."""
        ...

    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log a warning message."""
        ...

    def debug(self, msg: str, *args: object, **kwargs: object) -> None:
        """Log a debug message."""
        ...


class ConfigProvider(Protocol):
    """Protocol for fetching configuration values needed by agents."""

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a configuration value by key."""
        ...
