"""Execution API Models."""

from typing import Any

from pydantic import BaseModel, Field


class ExecutionStatusResponse(BaseModel):
    """Response model for fetching execution status."""

    execution_id: str
    status: str
    progress: int
    current_agent: str | None = None
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class ExecutionFindingsResponse(BaseModel):
    """Response model for fetching execution findings."""

    threat_score: float = Field(default=0.0)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    patches: list[dict[str, Any]] = Field(default_factory=list)
    severity_counts: dict[str, int] = Field(default_factory=dict)
    confidence_summary: dict[str, int] = Field(default_factory=dict)
