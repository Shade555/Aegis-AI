"""Base interface for security rules."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from aegis.application.agent.repository import RepositoryManifest
from aegis.domain.models.security import Finding


@dataclass
class FileNode:
    """Represents a file to be scanned."""

    path: str
    content: str


@dataclass
class RuleContext:
    """Context provided to a rule during analysis."""

    manifest: RepositoryManifest
    repo_path: Path

    def get_files(self) -> Generator[FileNode, None, None]:
        """Yields files to scan, ignoring heavy/irrelevant directories."""
        ignored = {
            ".git",
            "node_modules",
            ".next",
            "dist",
            "build",
            "__pycache__",
            ".venv",
            "venv",
            "coverage",
            "target",
        }

        queue = [self.repo_path]
        while queue:
            current_dir = queue.pop(0)
            try:
                for item in current_dir.iterdir():
                    if item.is_dir():
                        if item.name not in ignored and not item.name.startswith("."):
                            queue.append(item)
                    elif item.is_file():
                        try:
                            # We only care about text files for static analysis
                            content = item.read_text(encoding="utf-8")
                            yield FileNode(
                                path=item.relative_to(self.repo_path).as_posix(), content=content
                            )
                        except UnicodeDecodeError:
                            # Skip binary files
                            pass
            except PermissionError:
                pass


class SecurityRule(ABC):
    """Abstract base class for all static analysis security rules."""

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """A unique identifier for the rule (e.g., 'sql-injection-detector')."""
        pass

    @property
    @abstractmethod
    def target_languages(self) -> list[str]:
        """Languages this rule supports (e.g., ['python', 'javascript'])."""
        pass

    @abstractmethod
    async def analyze(self, context: RuleContext) -> list[Finding]:
        """Executes the rule against the repository manifest.

        Args:
            context: The context containing the repository manifest and file contents.

        Returns:
            A list of detected Findings.
        """
        pass
