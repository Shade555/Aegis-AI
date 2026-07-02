"""Finding domain entity, severity enumeration, and vulnerability type enumeration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class Severity(str, Enum):
    """CVSS-aligned severity classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(str, Enum):
    """Supported vulnerability categories for MVP."""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    HARDCODED_SECRET = "hardcoded_secret"
    INSECURE_DEPENDENCY = "insecure_dependency"
    UNSAFE_ENV_VAR = "unsafe_env_var"
    PROMPT_INJECTION = "prompt_injection"
    OTHER = "other"


class FindingStatus(str, Enum):
    """Resolution state of a finding."""

    OPEN = "open"
    PATCHED = "patched"
    ACCEPTED_RISK = "accepted_risk"
    FALSE_POSITIVE = "false_positive"


@dataclass
class Finding:
    """A single detected security vulnerability within an audit."""

    audit_id: UUID
    vulnerability_type: VulnerabilityType
    severity: Severity
    file_path: str
    title: str
    description: str
    id: UUID = field(default_factory=uuid4)
    agent_name: str = "security_analysis"
    cwe_id: str | None = None
    cve_id: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    code_snippet: str | None = None
    ai_explanation: str | None = None
    risk_score: float | None = None
    confidence: float = 0.8
    status: FindingStatus = FindingStatus.OPEN
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
