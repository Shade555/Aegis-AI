"""Models for the execution infrastructure."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from aegis.domain.events import AgentEventType


class ExecutionStatus(str, Enum):
    """The strict lifecycle states of an Execution Session."""

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExecutionEvent(BaseModel):
    """Standardized event emitted during execution."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_id: UUID
    agent_id: str | None = None
    agent_run_id: UUID | None = None
    event_type: AgentEventType | str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionSession(BaseModel):
    """The single source of truth for an active audit run."""

    execution_id: UUID = Field(default_factory=uuid4)
    audit_id: UUID
    project_id: UUID

    current_state: ExecutionStatus = ExecutionStatus.CREATED
    active_agent: str | None = None
    completed_agents: list[str] = Field(default_factory=list)
    failed_agents: list[str] = Field(default_factory=list)

    progress_percentage: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Store events directly in memory for MVP
    event_history: list[ExecutionEvent] = Field(default_factory=list)

    def transition_to(self, new_state: ExecutionStatus) -> None:
        """Safely transitions the session to a new state."""
        valid_transitions = {
            ExecutionStatus.CREATED: [
                ExecutionStatus.QUEUED,
                ExecutionStatus.RUNNING,
                ExecutionStatus.FAILED,
            ],
            ExecutionStatus.QUEUED: [ExecutionStatus.RUNNING, ExecutionStatus.FAILED],
            ExecutionStatus.RUNNING: [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED],
            ExecutionStatus.COMPLETED: [],
            ExecutionStatus.FAILED: [],
        }

        if new_state not in valid_transitions[self.current_state]:
            raise ValueError(f"Invalid transition from {self.current_state} to {new_state}")

        self.current_state = new_state
        if new_state == ExecutionStatus.RUNNING and not self.started_at:
            self.started_at = datetime.now(timezone.utc)
        elif new_state in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
            self.completed_at = datetime.now(timezone.utc)
