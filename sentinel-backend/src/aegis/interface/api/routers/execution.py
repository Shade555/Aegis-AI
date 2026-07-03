"""Execution status and monitoring endpoints."""

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from aegis.application.ai.prompts import PromptBuilder
from aegis.application.services.analysis import AnalysisService
from aegis.domain.models.patch import PatchCollection
from aegis.domain.models.security import ScanResult
from aegis.infrastructure.ai.gemini import MockGeminiService
from aegis.interface.api.dependencies import get_analysis_service
from aegis.interface.api.exceptions import AnalysisNotFoundError
from aegis.interface.api.models.execution import (
    ExecutionFindingsResponse,
    ExecutionStatusResponse,
)

router = APIRouter(prefix="/executions", tags=["execution"])


@router.get(
    "",
    summary="List Executions",
    description="Returns a list of all historical execution sessions.",
)
async def list_executions(
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> list[dict[str, Any]]:
    sessions = []
    # Sort by created_at descending
    all_sessions = list(analysis_service.session_manager._sessions.values())
    all_sessions.sort(key=lambda s: s.created_at or s.updated_at, reverse=True)
    
    for session in all_sessions:
        shared_state = analysis_service._shared_states.get(session.execution_id, {})
        
        # Get project name
        project_name = "Unknown Project"
        manifest = shared_state.get("repository_manifest", {})
        repo_path = shared_state.get("repo_path")
        if isinstance(manifest, dict) and manifest.get("project_name"):
            project_name = manifest.get("project_name")
        elif repo_path:
            from pathlib import Path
            project_name = Path(repo_path).name
            
        # Get threat score
        threat_score = 0.0
        findings_dict = analysis_service.get_findings(session.execution_id)
        if findings_dict:
            findings_list = findings_dict.get("findings", [])
            severity_weights = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1, "INFO": 0}
            for f in findings_list:
                sev = f.get("severity", "INFO")
                if hasattr(sev, "value"):
                    sev = sev.value
                threat_score += severity_weights.get(sev, 0)
            threat_score = min(100.0, float(threat_score))
            
        sessions.append({
            "execution_id": str(session.execution_id),
            "project_name": project_name,
            "status": session.current_state.value,
            "threat_score": threat_score,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": (session.completed_at or session.started_at or session.created_at).isoformat() if session.created_at else None,
            "progress": session.progress_percentage,
        })
        
    return sessions


@router.get(
    "/{execution_id}",
    response_model=ExecutionStatusResponse,
    summary="Get Execution Status",
    description="Returns the current status, progress, and timeline of the execution session.",
)
async def get_execution_status(
    execution_id: uuid.UUID, analysis_service: AnalysisService = Depends(get_analysis_service)
) -> dict[str, Any]:
    session = analysis_service.get_execution(execution_id)
    if not session:
        raise AnalysisNotFoundError(str(execution_id))

    timeline = []
    for evt in session.event_history:
        # event_type can be enum or str
        evt_type_str = (
            evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
        )
        timeline.append(
            {
                "timestamp": evt.timestamp.isoformat(),
                "agent_id": evt.agent_id,
                "event_type": evt_type_str,
                "message": evt.message,
                "metadata": evt.metadata,
            }
        )

    updated_at = session.completed_at or session.started_at or session.created_at

    return {
        "execution_id": str(session.execution_id),
        "status": session.current_state.value,
        "progress": session.progress_percentage,
        "current_agent": session.active_agent,
        "timeline": timeline,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


@router.get(
    "/{execution_id}/stream",
    summary="Stream Execution Events",
    description="Streams execution events in real-time via Server-Sent Events (SSE).",
)
async def stream_execution_events(
    execution_id: uuid.UUID, analysis_service: AnalysisService = Depends(get_analysis_service)
) -> StreamingResponse:
    session = analysis_service.get_execution(execution_id)
    if not session:
        raise AnalysisNotFoundError(str(execution_id))

    async def event_generator() -> Any:
        # Yield historical events first
        for evt in session.event_history:
            evt_type_str = (
                evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
            )
            data = {
                "timestamp": evt.timestamp.isoformat(),
                "agent_id": evt.agent_id,
                "event_type": evt_type_str,
                "message": evt.message,
                "metadata": evt.metadata,
                "progress": session.progress_percentage,
            }
            yield f"data: {json.dumps(data)}\n\n"

        # Subscribe to new events
        subscriber = analysis_service.session_manager.subscribe(session.audit_id)

        try:
            async for evt in subscriber:
                evt_type_str = (
                    evt.event_type.value
                    if hasattr(evt.event_type, "value")
                    else str(evt.event_type)
                )
                data = {
                    "timestamp": evt.timestamp.isoformat(),
                    "agent_id": evt.agent_id,
                    "event_type": evt_type_str,
                    "message": evt.message,
                    "metadata": evt.metadata,
                    "progress": session.progress_percentage,
                }
                yield f"data: {json.dumps(data)}\n\n"

                if evt_type_str in ("ExecutionCompleted", "ExecutionFailed"):
                    break
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get(
    "/{execution_id}/findings",
    response_model=ExecutionFindingsResponse,
    summary="Get Execution Findings",
    description="Returns the security findings detected during the execution session.",
)
async def get_execution_findings(
    execution_id: uuid.UUID, analysis_service: AnalysisService = Depends(get_analysis_service)
) -> dict[str, Any]:
    session = analysis_service.get_execution(execution_id)
    if not session:
        raise AnalysisNotFoundError(str(execution_id))

    findings = analysis_service.get_findings(execution_id)
    if not findings:
        return {
            "threat_score": 0.0,
            "findings": [],
            "patches": [],
            "severity_counts": {},
            "confidence_summary": {},
        }

    findings_list = findings.get("findings", [])
    
    severity_counts = {}
    threat_score = 0
    severity_weights = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1, "INFO": 0}
    
    for f in findings_list:
        sev = f.get("severity", "INFO")
        # Handle case where severity might be an Enum if not properly serialized
        if hasattr(sev, "value"):
            sev = sev.value
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        threat_score += severity_weights.get(sev, 0)

    findings["severity_counts"] = severity_counts
    findings["threat_score"] = min(100.0, float(threat_score))

    patch_dict = analysis_service._shared_states.get(execution_id, {}).get("patch_collection")
    patches = patch_dict.get("patches", []) if patch_dict else []
    findings["patches"] = patches

    return findings


@router.get(
    "/{execution_id}/manifest",
    summary="Get Repository Manifest",
    description="Returns the repository manifest extracted during the execution session.",
)
async def get_execution_manifest(
    execution_id: uuid.UUID, analysis_service: AnalysisService = Depends(get_analysis_service)
) -> dict[str, Any]:
    session = analysis_service.get_execution(execution_id)
    if not session:
        raise AnalysisNotFoundError(str(execution_id))

    manifest = analysis_service.get_manifest(execution_id)
    if not manifest:
        return {}

    # Map file extensions to readable language names for the frontend
    ext_to_lang = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++",
    }
    
    languages_used = manifest.get("languages_used", {})
    languages = set()
    for ext in languages_used.keys():
        if ext in ext_to_lang:
            languages.add(ext_to_lang[ext])
        else:
            languages.add(ext.lstrip(".").capitalize())
            
    manifest["languages"] = sorted(list(languages))
    
    shared_state = analysis_service._shared_states.get(execution_id, {})
    repo_path_str = shared_state.get("repo_path")
    if repo_path_str:
        from pathlib import Path
        manifest["project_name"] = Path(repo_path_str).name

    return manifest


@router.get(
    "/{execution_id}/reports/{format_type}",
    summary="Download Report",
    description="Downloads the generated execution report in the specified format (json, html, pdf).",
)
async def get_execution_report(
    execution_id: uuid.UUID,
    format_type: str,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> Response:
    if format_type not in ("json", "html", "pdf"):
        raise HTTPException(status_code=400, detail="Invalid format type.")

    session = analysis_service.get_execution(execution_id)
    if not session:
        raise AnalysisNotFoundError(str(execution_id))

    report = analysis_service.get_report(execution_id, format_type)
    if not report:
        raise HTTPException(status_code=404, detail="Report not generated or unavailable.")

    if format_type == "json":
        return Response(content=report, media_type="application/json")
    elif format_type == "html":
        return Response(content=report, media_type="text/html")
    elif format_type == "pdf":
        return Response(content=report, media_type="application/pdf")
    
    raise HTTPException(status_code=400, detail="Invalid format type.")


class ChatRequest(BaseModel):
    message: str


@router.post(
    "/{execution_id}/chat",
    summary="Chat with AI regarding execution results",
)
def chat_with_assistant(
    execution_id: uuid.UUID,
    request: ChatRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> dict[str, str]:
    """Interacts with the Gemini AI assistant about the analysis."""
    session = analysis_service.get_execution(execution_id)
    if not session:
        raise AnalysisNotFoundError(f"Execution {execution_id} not found.")

    findings_dict = analysis_service.get_findings(execution_id)
    patch_dict = analysis_service._shared_states.get(execution_id, {}).get("patch_collection")

    findings = ScanResult(**findings_dict).findings if findings_dict else []
    patches = PatchCollection(**patch_dict).patches if patch_dict else []

    prompt = PromptBuilder.build_chat_prompt(request.message, findings, patches)

    from aegis.config import settings
    from aegis.infrastructure.ai.gemini import GoogleGeminiService, MockGeminiService
    from pydantic import BaseModel

    class ChatResponseSchema(BaseModel):
        reply: str

    ai_service = GoogleGeminiService() if settings.gemini_api_key else MockGeminiService()
    try:
        response_data = ai_service.generate_json(prompt, schema=ChatResponseSchema)
        return {"reply": response_data.get("reply", "I'm sorry, I could not generate a response.")}
    except Exception as e:
        return {"reply": f"AI service is currently unavailable: {str(e)}"}
