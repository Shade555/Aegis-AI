import json
from uuid import uuid4

import pytest

from aegis.application.agent.models import AgentContext
from aegis.application.agent.reporting import ReportingAgent


class MockLogger:
    def info(self, msg):
        pass

    def error(self, msg):
        pass

    def warning(self, msg):
        pass

    def debug(self, msg):
        pass


class MockEventBus:
    async def publish(self, event):
        pass


@pytest.mark.asyncio
async def test_reporting_agent_generates_reports():
    event_bus = MockEventBus()
    agent = ReportingAgent("reporting_agent", event_bus, MockLogger())

    # Mock shared state with some dummy data
    shared_state = {
        "repository_manifest": {
            "project_type": "Node.js",
            "file_count": 10,
            "languages_used": {"JavaScript": 90, "HTML": 10},
            "dependency_managers": ["npm"],
        },
        "scan_result": {
            "findings": [
                {
                    "title": "SQL Injection",
                    "severity": "HIGH",
                    "description": "Found a potential SQLi.",
                    "explanation": "Agent reasoned this.",
                    "remediation_recommendation": "Use parameterized queries.",
                    "file_path": "index.js",
                    "line_start": 42,
                }
            ]
        },
    }

    context = AgentContext(
        project_id=uuid4(),
        audit_id=uuid4(),
        agent_run_id=uuid4(),
        repo_path="/dummy/path",
        shared_state=shared_state,
    )

    result = await agent.execute(context)

    assert result.status.value == "COMPLETE"

    # Assert JSON
    assert "report_json" in context.shared_state
    report_data = json.loads(context.shared_state["report_json"])
    assert report_data["threat_score"] == 5  # HIGH severity = 5
    assert len(report_data["findings"]) == 1

    # Assert HTML
    assert "report_html" in context.shared_state
    html_content = context.shared_state["report_html"]
    assert "SQL Injection" in html_content
    assert "Node.js" in html_content

    # Assert PDF
    assert "report_pdf" in context.shared_state
    pdf_content = context.shared_state["report_pdf"]
    assert isinstance(pdf_content, bytes)
