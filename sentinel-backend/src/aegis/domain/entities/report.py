"""Report domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Report:
    """A generated security audit report, available in PDF and JSON formats."""

    audit_id: UUID
    id: UUID = field(default_factory=uuid4)
    pdf_url: str | None = None
    json_url: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
