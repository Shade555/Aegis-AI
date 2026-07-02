"""Security analysis domain models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """The severity level of a security finding."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Confidence(str, Enum):
    """The confidence level of the analysis engine in the finding."""

    CERTAIN = "CERTAIN"
    FIRM = "FIRM"
    TENTATIVE = "TENTATIVE"


class AIFindingEnhancement(BaseModel):
    """AI-generated enrichment for a security finding."""

    explanation: str
    impact: str
    severity_justification: str
    secure_coding_recommendation: str
    best_practices: str


class Finding(BaseModel):
    """A detected security vulnerability."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    severity: Severity
    confidence: Confidence

    # Priority assigned by AI ranking
    ai_priority_score: int | None = None

    # Classification
    cwe_id: str | None = None
    owasp_category: str | None = None

    # Location
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    code_snippet: str | None = None

    # Remediation
    explanation: str
    remediation_recommendation: str

    # AI Enhancements
    ai_enhancement: AIFindingEnhancement | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class ScanResult(BaseModel):
    """The complete result of a security analysis phase."""

    audit_id: UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    findings: list[Finding] = Field(default_factory=list)

    def get_summary_stats(self) -> dict[str, int]:
        """Returns a count of findings by severity."""
        stats = {severity.value: 0 for severity in Severity}
        for finding in self.findings:
            stats[finding.severity.value] += 1
        return stats
