"""Repository Analysis Agent logic for indexing target codebases."""

from pathlib import Path

from pydantic import BaseModel, Field

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.models import AgentContext, AgentResult, AgentState
from aegis.domain.events import AgentEventType

IGNORED_DIRECTORIES = {
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

# Heuristics for package managers
PACKAGE_MANAGER_FILES = {
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "requirements.txt": "pip",
    "poetry.lock": "poetry",
}

# Heuristics for project types based on specific files
PROJECT_TYPE_FILES = {
    "next.config.js": "Next.js",
    "next.config.mjs": "Next.js",
    "next.config.ts": "Next.js",
    "svelte.config.js": "Svelte",
    "vite.config.ts": "Vite",
    "vite.config.js": "Vite",
    "manage.py": "Django",
    "fastapi": "FastAPI",  # typically inferred from requirements/imports, but keeping it simple
}

# Common config and env files we want to explicitly track
IMPORTANT_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
    "README.md",
}


class RepositoryManifest(BaseModel):
    """The single source of truth describing the analyzed repository."""

    project_type: str = "Unknown"
    languages_used: dict[str, int] = Field(default_factory=dict)
    frameworks: list[str] = Field(default_factory=list)
    dependency_managers: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    directory_tree: list[str] = Field(default_factory=list)
    file_count: int = 0
    source_file_count: int = 0
    configuration_files: list[str] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)
    environment_files: list[str] = Field(default_factory=list)


class RepositoryAgent(BaseAgent):
    """Agent responsible for understanding the target repository context."""

    async def execute(self, context: AgentContext) -> AgentResult:
        """Analyzes the repository filesystem and generates a manifest."""

        repo_path_str = context.shared_state.get("repo_path")
        if not repo_path_str:
            raise ValueError("Context shared_state must contain 'repo_path' for RepositoryAgent.")

        repo_path = Path(repo_path_str)
        if not repo_path.exists() or not repo_path.is_dir():
            raise ValueError(f"Repository path does not exist or is not a directory: {repo_path}")

        await self._emit_event(
            context=context,
            event_type=AgentEventType.PROGRESS,
            message="Repository Started",
            payload={"repo_path": str(repo_path)},
        )

        manifest = RepositoryManifest()
        queue: list[Path] = [repo_path]

        while queue:
            current_dir = queue.pop(0)

            # Emit progress per directory indexing (can be throttled in production, but we emit for testing)
            await self._emit_event(
                context=context,
                event_type=AgentEventType.PROGRESS,
                message=f"Directory Indexed: {current_dir.relative_to(repo_path)}",
            )

            try:
                for item in current_dir.iterdir():
                    if item.is_dir():
                        if item.name not in IGNORED_DIRECTORIES and not item.name.startswith("."):
                            queue.append(item)
                            manifest.directory_tree.append(item.relative_to(repo_path).as_posix())
                    elif item.is_file():
                        self._process_file(item, repo_path, manifest)
            except PermissionError:
                self.logger.warning(f"Permission denied accessing {current_dir}")

        # Post-process heuristic checks
        self._infer_frameworks(manifest)

        await self._emit_event(
            context=context,
            event_type=AgentEventType.PROGRESS,
            message="Framework Detected",
            payload={"frameworks": manifest.frameworks, "project_type": manifest.project_type},
        )

        await self._emit_event(
            context=context,
            event_type=AgentEventType.PROGRESS,
            message="Manifest Generated",
            payload={"file_count": manifest.file_count},
        )

        context.shared_state["repository_manifest"] = manifest.model_dump()

        await self._emit_event(
            context=context,
            event_type=AgentEventType.PROGRESS,
            message="Repository Completed",
        )

        return AgentResult(
            status=AgentState.COMPLETE,
            confidence=1.0,
            metadata={"manifest_generated": True, "files_indexed": manifest.file_count},
        )

    def _process_file(self, file_path: Path, root_path: Path, manifest: RepositoryManifest) -> None:
        """Analyze a single file and update the manifest accordingly."""
        manifest.file_count += 1

        # Language tally by extension
        ext = file_path.suffix.lower()
        if ext in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"}:
            manifest.source_file_count += 1
            manifest.languages_used[ext] = manifest.languages_used.get(ext, 0) + 1

        # Important Config files
        if file_path.name in IMPORTANT_FILES:
            manifest.configuration_files.append(file_path.relative_to(root_path).as_posix())

            if file_path.name == "package.json":
                try:
                    import json
                    with open(file_path, "r", encoding="utf-8") as f:
                        pkg = json.load(f)
                    
                    deps = pkg.get("dependencies", {})
                    dev_deps = pkg.get("devDependencies", {})
                    all_deps = {**deps, **dev_deps}
                    
                    manifest.dependencies.extend(list(all_deps.keys()))
                    
                    if "next" in all_deps and "Next.js" not in manifest.frameworks:
                        manifest.frameworks.append("Next.js")
                    if "react" in all_deps and "React" not in manifest.frameworks:
                        manifest.frameworks.append("React")
                    if "vue" in all_deps and "Vue" not in manifest.frameworks:
                        manifest.frameworks.append("Vue")
                    if "svelte" in all_deps and "Svelte" not in manifest.frameworks:
                        manifest.frameworks.append("Svelte")
                    if "express" in all_deps and "Express" not in manifest.frameworks:
                        manifest.frameworks.append("Express")
                    if "nestjs" in all_deps or "@nestjs/core" in all_deps:
                        if "NestJS" not in manifest.frameworks:
                            manifest.frameworks.append("NestJS")
                except Exception:
                    # Fallback if parsing fails
                    if "React" not in manifest.frameworks:
                        manifest.frameworks.append("React")
        if "env" in file_path.name.lower():
            manifest.environment_files.append(file_path.relative_to(root_path).as_posix())

        # Package Managers
        if file_path.name in PACKAGE_MANAGER_FILES:
            pm = PACKAGE_MANAGER_FILES[file_path.name]
            if pm not in manifest.dependency_managers:
                manifest.dependency_managers.append(pm)

        # Explicit framework files
        if file_path.name in PROJECT_TYPE_FILES:
            fw = PROJECT_TYPE_FILES[file_path.name]
            if fw not in manifest.frameworks:
                manifest.frameworks.append(fw)

        # Basic Entrypoints (main.py, index.js, app.py)
        if file_path.name in {"main.py", "app.py", "index.js", "index.ts"}:
            manifest.entry_points.append(file_path.relative_to(root_path).as_posix())

    def _infer_frameworks(self, manifest: RepositoryManifest) -> None:
        """Consolidate the detected signals to determine primary project type."""
        if "Next.js" in manifest.frameworks:
            manifest.project_type = "Next.js"
        elif "Django" in manifest.frameworks:
            manifest.project_type = "Django"
        elif (
            "requirements.txt" in [Path(p).name for p in manifest.configuration_files]
            or ".py" in manifest.languages_used
        ):
            # Basic fallback
            if manifest.project_type == "Unknown":
                manifest.project_type = "Python"
        elif ".ts" in manifest.languages_used or ".js" in manifest.languages_used:
            if manifest.project_type == "Unknown":
                manifest.project_type = "Node.js"
