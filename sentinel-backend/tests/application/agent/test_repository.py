"""Unit tests for the RepositoryAgent."""

import uuid
from pathlib import Path

import pytest

from aegis.application.agent.models import AgentContext, AgentState
from aegis.application.agent.repository import RepositoryAgent
from aegis.domain.events import AgentEventType
from tests.application.agent.test_framework import MockEventBus, MockLogger


@pytest.fixture
def agent() -> RepositoryAgent:
    return RepositoryAgent(name="repository_agent", event_bus=MockEventBus(), logger=MockLogger())


@pytest.fixture
def context() -> AgentContext:
    return AgentContext(
        audit_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        agent_run_id=uuid.uuid4(),
        shared_state={},
    )


@pytest.mark.asyncio
async def test_invalid_path(agent: RepositoryAgent, context: AgentContext) -> None:
    """Agent fails gracefully if repo_path is missing or invalid."""

    # Missing repo_path
    result = await agent.run(context)
    assert result.status == AgentState.FAILED
    assert "must contain 'repo_path'" in str(result.error_message)

    # Invalid repo_path
    context.shared_state["repo_path"] = "/does/not/exist/ever"
    result = await agent.run(context)
    assert result.status == AgentState.FAILED
    assert "does not exist or is not a directory" in str(result.error_message)


@pytest.mark.asyncio
async def test_empty_repository(
    agent: RepositoryAgent, context: AgentContext, tmp_path: Path
) -> None:
    """Agent handles completely empty directories cleanly."""
    context.shared_state["repo_path"] = str(tmp_path)
    result = await agent.run(context)

    assert result.status == AgentState.COMPLETE
    manifest = context.shared_state["repository_manifest"]
    assert manifest["file_count"] == 0
    assert manifest["source_file_count"] == 0
    assert manifest["project_type"] == "Unknown"

    # Events
    event_types = [e.event_type for e in agent.event_bus.events]  # type: ignore
    assert AgentEventType.STARTED in event_types
    assert AgentEventType.COMPLETE in event_types


@pytest.mark.asyncio
async def test_ignored_directories(
    agent: RepositoryAgent, context: AgentContext, tmp_path: Path
) -> None:
    """Agent strictly avoids indexing ignored directories."""

    # Create valid file
    (tmp_path / "main.py").write_text("print('hello')")

    # Create ignored directories and nested files
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("ignored")

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "index.js").write_text("ignored")

    context.shared_state["repo_path"] = str(tmp_path)
    result = await agent.run(context)

    assert result.status == AgentState.COMPLETE
    manifest = context.shared_state["repository_manifest"]

    # Only main.py should be counted
    assert manifest["file_count"] == 1
    assert manifest["source_file_count"] == 1
    assert manifest["languages_used"] == {".py": 1}
    assert ".git" not in manifest["directory_tree"]
    assert "node_modules" not in manifest["directory_tree"]


@pytest.mark.asyncio
async def test_python_repository(
    agent: RepositoryAgent, context: AgentContext, tmp_path: Path
) -> None:
    """Agent accurately detects Python projects."""

    (tmp_path / "requirements.txt").write_text("pytest")
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "utils.py").write_text("pass")

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("pass")

    context.shared_state["repo_path"] = str(tmp_path)
    result = await agent.run(context)

    assert result.status == AgentState.COMPLETE
    manifest = context.shared_state["repository_manifest"]

    assert manifest["project_type"] == "Python"
    assert manifest["dependency_managers"] == ["pip"]
    assert manifest["languages_used"] == {".py": 3}
    assert "requirements.txt" in manifest["configuration_files"]
    assert "main.py" in manifest["entry_points"]
    assert "src/app.py" in manifest["entry_points"]
    assert "src" in manifest["directory_tree"]


@pytest.mark.asyncio
async def test_nextjs_repository(
    agent: RepositoryAgent, context: AgentContext, tmp_path: Path
) -> None:
    """Agent accurately detects Next.js (Node) projects."""

    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "yarn.lock").write_text("")
    (tmp_path / "next.config.mjs").write_text("")
    (tmp_path / ".env.local").write_text("KEY=val")

    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "page.tsx").write_text("")
    (app_dir / "layout.tsx").write_text("")

    context.shared_state["repo_path"] = str(tmp_path)
    result = await agent.run(context)

    assert result.status == AgentState.COMPLETE
    manifest = context.shared_state["repository_manifest"]

    assert manifest["project_type"] == "Next.js"
    assert "yarn" in manifest["dependency_managers"]
    assert manifest["languages_used"] == {".tsx": 2}
    assert ".env.local" in manifest["environment_files"]
    assert "Next.js" in manifest["frameworks"]
    assert "React" in manifest["frameworks"]


@pytest.mark.asyncio
async def test_mixed_repository(
    agent: RepositoryAgent, context: AgentContext, tmp_path: Path
) -> None:
    """Agent accurately profiles monorepos or mixed-language repos."""

    # Python backend
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "manage.py").write_text("")
    (backend / "settings.py").write_text("")

    # React frontend
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text("")
    (frontend / "index.js").write_text("")

    context.shared_state["repo_path"] = str(tmp_path)
    result = await agent.run(context)

    assert result.status == AgentState.COMPLETE
    manifest = context.shared_state["repository_manifest"]

    assert manifest["project_type"] == "Django"  # By priority in our basic heuristic
    assert "Django" in manifest["frameworks"]
    assert "React" in manifest["frameworks"]
    assert manifest["languages_used"] == {".py": 2, ".js": 1}
    assert "backend" in manifest["directory_tree"]
    assert "frontend" in manifest["directory_tree"]
    assert "frontend/index.js" in manifest["entry_points"]
