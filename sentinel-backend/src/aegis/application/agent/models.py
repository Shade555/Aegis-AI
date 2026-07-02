"""Core data models for agent execution state and task queueing."""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Lifecycle states of an agent's execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class AgentContext(BaseModel):
    """Execution context provided to an agent when it runs.

    Contains all the necessary identifiers to read/write state and emit events.
    """

    audit_id: UUID
    project_id: UUID
    agent_run_id: UUID
    # Shared state that agents might need (e.g. repo path, previous agent outputs)
    shared_state: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    """The structured output returned by an agent upon completion."""

    status: AgentState
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkItem(BaseModel):
    """A serialized instruction for an agent to perform a specific task.

    Used to pass work through a job queue (like ARQ).
    """

    audit_id: UUID
    project_id: UUID
    agent_run_id: UUID
    agent_name: str
    payload: dict[str, Any] = Field(default_factory=dict)
