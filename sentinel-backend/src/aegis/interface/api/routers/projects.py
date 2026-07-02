"""Projects Router."""

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile

from aegis.application.services.analysis import AnalysisService
from aegis.interface.api.dependencies import get_analysis_service
from aegis.interface.api.exceptions import InvalidProjectStateError
from aegis.interface.api.models.projects import AnalyzeProjectResponse

router = APIRouter()


@router.post(
    "/projects/analyze",
    response_model=AnalyzeProjectResponse,
    summary="Start repository analysis",
    description="Starts an analysis session on a local path or an uploaded ZIP file.",
    tags=["projects"],
)
async def analyze_project(
    background_tasks: BackgroundTasks,
    local_path: Optional[str] = Form(None, description="Absolute path to the local repository."),
    demo_id: Optional[str] = Form(None, description="ID of the demo repository to analyze."),
    file: Optional[UploadFile] = File(None, description="A ZIP file containing the repository."),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> dict[str, Any]:
    """Start an analysis session."""
    import os
    from pathlib import Path

    if demo_id:
        base_dir = Path.cwd()
        if demo_id == "quickshop":
            local_path = str(base_dir / "demo_repos" / "quickshop_api")
        elif demo_id == "healthsync":
            local_path = str(base_dir / "demo_repos" / "healthsync_portal")
        elif demo_id == "fintrust":
            local_path = str(base_dir / "demo_repos" / "fintrust_platform")

    if not local_path and not file:
        raise InvalidProjectStateError(
            "Must provide either local_path, demo_id, or an uploaded file."
        )

    # -------------------------------------------------------------------------
    # Docker Path Rewrite Hack
    # If the backend is running in Docker, it cannot access C:\Users\...
    # We mounted the Kaggle_agent_dev folder to /app/workspace.
    # So if we see a path containing Kaggle_agent_dev, we rewrite it.
    # -------------------------------------------------------------------------
    if local_path and "Kaggle_agent_dev" in local_path:
        # Standardize slashes
        normalized_path = local_path.replace("\\", "/")
        if "Kaggle_agent_dev/" in normalized_path:
            relative_part = normalized_path.split("Kaggle_agent_dev/")[-1]
            # Verify if we are inside docker by checking if /app/workspace exists
            if Path("/app/workspace").exists():
                local_path = str(Path("/app/workspace") / relative_part)

    try:
        execution_id = await analysis_service.start_analysis(
            project_path=local_path, upload_file=file, background_tasks=background_tasks
        )
    except ValueError as e:
        raise InvalidProjectStateError(str(e))

    return {"execution_id": str(execution_id), "status": "PENDING"}
