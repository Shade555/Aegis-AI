"""Analysis Service."""

import logging
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, UploadFile

from aegis.application.agent.enhancement import AIEnhancementAgent
from aegis.application.agent.patch import PatchGenerationAgent
from aegis.application.agent.ports import Logger
from aegis.application.agent.registry import WorkItemRegistry
from aegis.application.agent.reporting import ReportingAgent
from aegis.application.agent.repository import RepositoryAgent
from aegis.application.agent.security import SecurityAnalysisAgent
from aegis.application.agent.supervisor import SupervisorAgent
from aegis.application.execution.engine import AgentExecutor
from aegis.application.execution.manager import SessionManager
from aegis.application.execution.models import ExecutionSession


class PrintLogger(Logger):
    """Simple logger for the execution engine."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("aegis.execution")

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.error(msg, *args, **kwargs)


class AnalysisService:
    """Orchestrates analysis sessions."""

    def __init__(self, session_manager: SessionManager) -> None:
        self.session_manager = session_manager
        self._shared_states: dict[uuid.UUID, dict[str, Any]] = {}

        # Initialize registry and register agents
        self.registry = WorkItemRegistry()
        self.registry.register(
            "supervisor_agent", lambda eb, logger: SupervisorAgent("supervisor", eb, logger)
        )
        self.registry.register(
            "repository_agent", lambda eb, logger: RepositoryAgent("repository", eb, logger)
        )
        # Use real Gemini if key is provided, otherwise mock
        import os
        from aegis.config import settings
        from aegis.infrastructure.ai.gemini import GoogleGeminiService, MockGeminiService
        gemini_svc = GoogleGeminiService() if settings.gemini_api_key else MockGeminiService()
        
        self.registry.register(
            "security_agent", lambda eb, logger: SecurityAnalysisAgent("security", eb, logger, gemini_service=gemini_svc)
        )
        self.registry.register(
            "patch_agent", lambda eb, logger: PatchGenerationAgent("patch", eb, logger)
        )
        self.registry.register(
            "enhancement_agent",
            lambda eb, logger: AIEnhancementAgent("enhancement", eb, logger, gemini_svc),
        )
        self.registry.register(
            "reporting_agent", lambda eb, logger: ReportingAgent("documentation", eb, logger)
        )

        self.logger: Logger = PrintLogger()
        self.executor = AgentExecutor(registry=self.registry, logger=self.logger)
        self._load_from_disk()

    def _get_storage_path(self) -> Path:
        data_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / "sessions.json"

    def _save_to_disk(self) -> None:
        import json
        storage_path = self._get_storage_path()
        data = []
        for exec_id, session in self.session_manager._sessions.items():
            state = self._shared_states.get(exec_id, {})
            safe_state = {}
            for k, v in state.items():
                if k not in ("report_pdf", "report_html"):
                    safe_state[k] = v
            
            data.append({
                "session": session.model_dump(mode="json"),
                "shared_state": safe_state
            })
        
        with open(storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
    def _load_from_disk(self) -> None:
        import json
        storage_path = self._get_storage_path()
        if not storage_path.exists():
            return
            
        try:
            with open(storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for item in data:
                session_dict = item.get("session")
                state_dict = item.get("shared_state", {})
                if session_dict:
                    session = ExecutionSession.model_validate(session_dict)
                    self.session_manager.register_session(session)
                    self._shared_states[session.audit_id] = state_dict
        except Exception as e:
            self.logger.error(f"Error loading sessions from disk: {e}")

    async def start_analysis(
        self,
        project_path: str | None,
        upload_file: UploadFile | None,
        background_tasks: BackgroundTasks,
    ) -> uuid.UUID:
        """Starts a new analysis session."""

        if upload_file and upload_file.filename:
            # Handle uploaded ZIP file
            temp_dir = tempfile.mkdtemp(prefix="aegis_")
            zip_path = Path(temp_dir) / upload_file.filename

            with open(zip_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)

            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile:
                raise ValueError("Uploaded file is not a valid ZIP archive.")

            repo_path = Path(temp_dir)
        elif project_path:
            repo_path = Path(project_path)
            if not repo_path.exists() or not repo_path.is_dir():
                raise ValueError("Provided project_path does not exist or is not a directory.")
        else:
            raise ValueError("Must provide either project_path or upload_file.")

        execution_id = uuid.uuid4()
        session = ExecutionSession(
            audit_id=execution_id, project_id=uuid.uuid4(), execution_id=execution_id
        )

        self.session_manager.register_session(session)

        shared_state = {"repo_path": str(repo_path)}
        self._shared_states[execution_id] = shared_state

        agent_names = [
            "supervisor_agent",
            "repository_agent",
            "security_agent",
            "patch_agent",
            "enhancement_agent",
            "reporting_agent",
        ]

        # Dispatch execution in background
        async def run_and_save():
            await self.executor.run_session(session, agent_names, shared_state)
            self._save_to_disk()

        background_tasks.add_task(run_and_save)

        return execution_id

    def get_execution(self, execution_id: uuid.UUID) -> ExecutionSession | None:
        """Retrieves an execution session by ID."""
        return self.session_manager.get_session(execution_id)

    def get_findings(self, execution_id: uuid.UUID) -> dict[str, Any] | None:
        """Retrieves the latest scan result from a session."""
        session = self.get_execution(execution_id)
        if not session:
            return None

        shared_state = self._shared_states.get(execution_id, {})
        scan_result = shared_state.get("scan_result")
        if isinstance(scan_result, dict):
            return dict(scan_result)

        return None

    def get_manifest(self, execution_id: uuid.UUID) -> dict[str, Any] | None:
        """Retrieves the repository manifest from a session."""
        session = self.get_execution(execution_id)
        if not session:
            return None

        shared_state = self._shared_states.get(execution_id, {})
        manifest = shared_state.get("repository_manifest")
        if isinstance(manifest, dict):
            return dict(manifest)

        return None

    def get_report(self, execution_id: uuid.UUID, format_type: str) -> Any:
        """Retrieves a generated report."""
        session = self.get_execution(execution_id)
        if not session:
            return None

        shared_state = self._shared_states.get(execution_id, {})

        if format_type == "json":
            return shared_state.get("report_json")
        elif format_type == "html":
            return shared_state.get("report_html")
        elif format_type == "pdf":
            return shared_state.get("report_pdf")

        return None
