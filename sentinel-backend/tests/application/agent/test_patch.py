"""Unit tests for the Patch Generation Agent and generators."""

import uuid

import pytest

from aegis.application.agent.models import AgentContext
from aegis.application.agent.patch import (
    DeterministicPatchGenerator,
    PatchGenerationAgent,
    UnifiedDiffGenerator,
)
from aegis.domain.events import AgentEventType
from aegis.domain.models.security import Confidence, Finding, ScanResult, Severity


class MockEventBus:
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)


class MockLogger:
    def info(self, msg, *args, **kwargs):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass


def test_unified_diff_generator():
    """Test generating a unified diff."""
    original = 'def query(user_id):\n    return f"SELECT * FROM users WHERE id = {user_id}"\n'
    patched = 'def query(user_id):\n    return "SELECT * FROM users WHERE id = %s", (user_id,)\n'

    diff = UnifiedDiffGenerator.generate(
        original_snippet=original, patched_snippet=patched, file_path="src/db.py"
    )

    assert "--- a/src/db.py" in diff
    assert "+++ b/src/db.py" in diff
    assert '-    return f"SELECT * FROM users WHERE id = {user_id}"' in diff
    assert '+    return "SELECT * FROM users WHERE id = %s", (user_id,)' in diff


def test_deterministic_patch_generator_sql_injection():
    """Test patching a SQL injection finding."""
    finding = Finding(
        title="Potential SQL Injection",
        description="Unsafe SQL",
        severity=Severity.HIGH,
        confidence=Confidence.TENTATIVE,
        cwe_id="CWE-89",
        file_path="app.py",
        code_snippet="query = f\"SELECT * FROM users WHERE username = '{user_input}'\"",
        explanation="Using f-strings to build SQL...",
        remediation_recommendation="Use parameterized queries...",
    )

    generator = DeterministicPatchGenerator()
    patch = generator.generate_patch(finding)

    assert patch is not None
    assert patch.finding_id == finding.id
    assert patch.files_changed == 1
    assert patch.estimated_review_time > 0
    assert "SELECT * FROM users WHERE username = '%s'" in patch.patched_snippet
    assert patch.explanation.problem is not None
    assert patch.explanation.solution is not None


def test_deterministic_patch_generator_hardcoded_secret():
    """Test patching a hardcoded secret."""
    finding = Finding(
        title="Hardcoded Secret",
        description="Secret found",
        severity=Severity.CRITICAL,
        confidence=Confidence.CERTAIN,
        cwe_id="CWE-798",
        file_path="config.py",
        code_snippet="API_KEY = '12345secret'",
        explanation="Hardcoded secret...",
        remediation_recommendation="Move to env...",
    )

    generator = DeterministicPatchGenerator()
    patch = generator.generate_patch(finding)

    assert patch is not None
    assert 'os.environ.get("API_KEY")' in patch.patched_snippet


@pytest.mark.asyncio
async def test_patch_generation_agent():
    """Test the PatchGenerationAgent execution pipeline."""
    audit_id = uuid.uuid4()
    run_id = uuid.uuid4()
    context = AgentContext(
        audit_id=audit_id, run_id=run_id, project_id=uuid.uuid4(), agent_run_id=uuid.uuid4()
    )

    finding1 = Finding(
        title="Potential SQL Injection",
        description="Unsafe SQL",
        severity=Severity.HIGH,
        confidence=Confidence.TENTATIVE,
        cwe_id="CWE-89",
        file_path="app.py",
        code_snippet="query = f\"SELECT * FROM users WHERE username = '{user_input}'\"",
        explanation="Using f-strings to build SQL...",
        remediation_recommendation="Use parameterized queries...",
    )

    finding2 = Finding(
        title="Unknown Issue",
        description="Something else",
        severity=Severity.LOW,
        confidence=Confidence.TENTATIVE,
        cwe_id="CWE-999",
        file_path="app.py",
        code_snippet="x = 1",
        explanation="...",
        remediation_recommendation="...",
    )

    scan_result = ScanResult(audit_id=audit_id, findings=[finding1, finding2])
    context.shared_state["scan_result"] = scan_result.model_dump(mode="json")
    context.shared_state["repo_path"] = "/tmp/repo"

    bus = MockEventBus()
    logger = MockLogger()

    agent = PatchGenerationAgent("patch_agent", bus, logger)
    result = await agent.execute(context)

    assert result.status == "COMPLETE"
    assert result.metadata["total_patches"] == 1

    # Verify state was mutated
    assert "patch_collection" in context.shared_state
    collection_data = context.shared_state["patch_collection"]
    assert len(collection_data["patches"]) == 1

    # Verify events
    event_types = [e.event_type.value for e in bus.events]
    assert AgentEventType.PATCH_GENERATION_STARTED.value in event_types
    assert AgentEventType.PATCH_GENERATED.value in event_types
    assert AgentEventType.PATCH_VALIDATED.value in event_types
    assert AgentEventType.PATCH_SKIPPED.value in event_types
    assert AgentEventType.PATCH_GENERATION_COMPLETED.value in event_types
