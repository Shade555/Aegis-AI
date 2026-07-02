"""SQLAlchemy ORM models for all Aegis AI database tables.

All models use SQLAlchemy 2.0 style with Mapped[] annotations.
The Base is imported from connection.py so Alembic can discover all models
through a single import of this module.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aegis.infrastructure.database.connection import Base


class UserModel(Base):
    """Clerk-authenticated user, synced via Clerk webhook."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clerk_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    projects: Mapped[list["ProjectModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ProjectModel(Base):
    """A software repository registered by a user for auditing."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    repo_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    # 'github' | 'upload'
    repo_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # {"python": 0.72, "javascript": 0.28}
    language_profile: Mapped[Optional[dict[str, float]]] = mapped_column(JSONB, nullable=True)
    # ["django", "react"]
    framework_tags: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship(back_populates="projects")
    audits: Mapped[list["AuditModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class AuditModel(Base):
    """A single security audit run against a project."""

    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # pending | planning | running | awaiting_approval | patching | complete | failed | cancelled
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    threat_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # The Supervisor's JSON execution DAG
    agent_plan: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["ProjectModel"] = relationship(back_populates="audits")
    agent_runs: Mapped[list["AgentRunModel"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    agent_events: Mapped[list["AgentEventModel"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    findings: Mapped[list["FindingModel"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    patches: Mapped[list["PatchModel"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    report: Mapped[Optional["ReportModel"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan", uselist=False
    )


class AgentRunModel(Base):
    """Tracks one agent's execution within an audit."""

    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # pending | running | complete | failed | skipped
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Agent's self-reported confidence in its output (0.0–1.0)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Agent-specific structured output metadata
    meta_data: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)

    audit: Mapped["AuditModel"] = relationship(back_populates="agent_runs")
    events: Mapped[list["AgentEventModel"]] = relationship(
        back_populates="agent_run", cascade="all, delete-orphan"
    )


class AgentEventModel(Base):
    """A single event emitted by an agent — the source of the activity timeline."""

    __tablename__ = "agent_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # STARTED | PROGRESS | FINDING | COMPLETE | ERROR
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Event-type-specific structured payload
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    audit: Mapped["AuditModel"] = relationship(back_populates="agent_events")
    agent_run: Mapped[Optional["AgentRunModel"]] = relationship(back_populates="events")


class FindingModel(Base):
    """A detected security vulnerability within an audit."""

    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="security_analysis"
    )
    vulnerability_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # critical | high | medium | low | info
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    cwe_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cve_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    line_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    line_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # CVSS-style 0.0–10.0
    risk_score: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    # Agent confidence 0.00–1.00
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    # open | patched | accepted_risk | false_positive
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    meta_data: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    audit: Mapped["AuditModel"] = relationship(back_populates="findings")
    patch: Mapped[Optional["PatchModel"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", uselist=False
    )


class PatchModel(Base):
    """A unified diff patch proposed to fix a specific finding."""

    __tablename__ = "patches"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    diff: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    # proposed | approved | rejected | applied | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="proposed")
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    finding: Mapped["FindingModel"] = relationship(back_populates="patch")
    audit: Mapped["AuditModel"] = relationship(back_populates="patches")


class ReportModel(Base):
    """Generated audit report with links to PDF and JSON artifacts."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    json_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    audit: Mapped["AuditModel"] = relationship(back_populates="report")
