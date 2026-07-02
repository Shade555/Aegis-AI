"""Patch domain models."""

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from aegis.domain.models.security import Confidence


class PatchQuality(str, Enum):
    """The quality or reliability of the generated patch."""

    PRODUCTION_READY = "PRODUCTION_READY"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    EXPERIMENTAL = "EXPERIMENTAL"


class PatchExplanation(BaseModel):
    """Structured explanation for a generated patch."""

    problem: str
    solution: str
    impact: str
    manual_review_notes: str | None = None
    confidence_level: Confidence


class AIPatchEnhancement(BaseModel):
    """AI-generated enrichment for a generated patch."""

    explanation: str
    why_preferred: str
    alternative_approaches: str
    possible_trade_offs: str


class Patch(BaseModel):
    """A proposed fix for a security finding."""

    id: UUID = Field(default_factory=uuid4)
    finding_id: UUID
    file_path: str
    original_snippet: str
    patched_snippet: str
    unified_diff: str
    explanation: PatchExplanation

    # Impact and review
    quality: PatchQuality
    estimated_review_time: int  # In minutes
    files_changed: int = 1
    insertions: int = 0
    deletions: int = 0
    requires_manual_review: bool

    # AI Enhancements
    ai_enhancement: AIPatchEnhancement | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class PatchCollection(BaseModel):
    """A collection of generated patches for a repository."""

    patches: list[Patch] = Field(default_factory=list)
