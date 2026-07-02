import uuid

from fastapi.testclient import TestClient

from aegis.application.execution.models import ExecutionEvent, ExecutionSession
from aegis.main import app

client = TestClient(app)

from unittest.mock import MagicMock


def test_sse_streaming():
    # Mock get_analysis_service
    from aegis.application.services.analysis import AnalysisService
    from aegis.interface.api.dependencies import get_analysis_service

    mock_service = MagicMock(spec=AnalysisService)

    # Setup session
    audit_id = uuid.uuid4()
    execution_id = uuid.uuid4()
    session = ExecutionSession(
        audit_id=audit_id, execution_id=execution_id, project_id=uuid.uuid4()
    )

    # Add historical events
    evt1 = ExecutionEvent(
        execution_id=execution_id, event_type="ExecutionStarted", message="Started"
    )
    session.event_history.append(evt1)

    mock_service.get_execution.return_value = session

    # Create mock subscriber
    async def mock_subscriber():
        evt2 = ExecutionEvent(execution_id=execution_id, event_type="PROGRESS", message="Working")
        yield evt2
        evt3 = ExecutionEvent(
            execution_id=execution_id, event_type="ExecutionCompleted", message="Done"
        )
        yield evt3

    mock_service.session_manager = MagicMock()
    mock_service.session_manager.subscribe.return_value = mock_subscriber()

    app.dependency_overrides[get_analysis_service] = lambda: mock_service

    # We use stream request in test client
    with client.stream("GET", f"/executions/{execution_id}/stream") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        content = ""
        for chunk in response.iter_text():
            content += chunk

        # Validate SSE format
        events = content.strip().split("\n\n")
        assert len(events) == 3

        assert "ExecutionStarted" in events[0]
        assert "PROGRESS" in events[1]
        assert "ExecutionCompleted" in events[2]

    app.dependency_overrides.clear()
