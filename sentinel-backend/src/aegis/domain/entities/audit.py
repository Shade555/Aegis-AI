"""Audit domain entity and status enumeration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class AuditStatus(str, Enum):
    """Lifecycle states for a security audit run."""

    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    PATCHING = "patching"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Audit:
    """Represents a single security audit run against a project."""

    project_id: UUID
    metadata: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    status: AuditStatus = AuditStatus.PENDING
    threat_score: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    agent_plan: dict[str, Any] | None = None
    summary: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
