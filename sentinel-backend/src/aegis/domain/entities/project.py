"""Project domain entity and repository type enumeration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class RepoType(str, Enum):
    """How the repository was provided by the user."""

    GITHUB = "github"
    UPLOAD = "upload"


@dataclass
class Project:
    """A software project registered by a user for security auditing."""

    user_id: UUID
    name: str
    repo_type: RepoType
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    repo_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    framework_tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
