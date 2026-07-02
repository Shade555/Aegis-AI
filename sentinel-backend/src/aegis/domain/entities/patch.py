"""Patch domain entity and status enumeration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class PatchStatus(str, Enum):
    """Lifecycle states for a proposed code patch."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


@dataclass
class Patch:
    """A unified diff patch proposed to fix a specific finding."""

    finding_id: UUID
    audit_id: UUID
    diff: str
    file_path: str
    justification: str
    id: UUID = field(default_factory=uuid4)
    status: PatchStatus = PatchStatus.PROPOSED
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    applied_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
