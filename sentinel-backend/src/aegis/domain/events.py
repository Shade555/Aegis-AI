"""Domain events used across the Aegis AI platform."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentEventType(str, Enum):
    """Types of events emitted by agents during an audit."""

    STARTED = "STARTED"
    PROGRESS = "PROGRESS"
    FINDING = "FINDING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

    # Security Analysis specific events
    SECURITY_SCAN_STARTED = "SECURITY_SCAN_STARTED"
    RULE_STARTED = "RULE_STARTED"
    FINDING_DETECTED = "FINDING_DETECTED"
    RULE_COMPLETED = "RULE_COMPLETED"
    SECURITY_SCAN_COMPLETED = "SECURITY_SCAN_COMPLETED"

    # Patch Generation specific events
    PATCH_GENERATION_STARTED = "PATCH_GENERATION_STARTED"
    PATCH_GENERATED = "PATCH_GENERATED"
    PATCH_SKIPPED = "PATCH_SKIPPED"
    PATCH_VALIDATED = "PATCH_VALIDATED"
    PATCH_GENERATION_COMPLETED = "PATCH_GENERATION_COMPLETED"


class AgentEvent(BaseModel):
    """Represents an observable event emitted by an agent during execution.

    These events form the audit trail and power the real-time SSE stream.
    """

    id: UUID = Field(default_factory=uuid4)
    audit_id: UUID
    agent_run_id: UUID | None = None
    agent_name: str
    event_type: AgentEventType
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
