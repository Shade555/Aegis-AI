"""Unit tests for the Security Rule Engine."""

from pathlib import Path

import pytest

from aegis.application.agent.repository import RepositoryManifest
from aegis.application.security.engine import RuleEngine
from aegis.application.security.rules.base import RuleContext, SecurityRule
from aegis.domain.models.security import Confidence, Finding, Severity


class DummyRule(SecurityRule):
    @property
    def rule_name(self) -> str:
        return "dummy-rule"

    @property
    def target_languages(self) -> list[str]:
        return ["*"]

    async def analyze(self, context: RuleContext) -> list[Finding]:
        return [
            Finding(
                title="Dummy",
                description="Dummy finding",
                severity=Severity.LOW,
                confidence=Confidence.CERTAIN,
                file_path="dummy.txt",
                explanation="None",
                remediation_recommendation="None",
            )
        ]


class FailingRule(SecurityRule):
    @property
    def rule_name(self) -> str:
        return "failing-rule"

    @property
    def target_languages(self) -> list[str]:
        return ["*"]

    async def analyze(self, context: RuleContext) -> list[Finding]:
        raise RuntimeError("I crashed!")


@pytest.mark.asyncio
async def test_rule_engine_execution() -> None:
    engine = RuleEngine([DummyRule()])
    manifest = RepositoryManifest()
    context = RuleContext(manifest=manifest, repo_path=Path("/repo"))

    findings = await engine.run(context)
    assert len(findings) == 1
    assert findings[0].title == "Dummy"


@pytest.mark.asyncio
async def test_rule_engine_handles_crashes() -> None:
    engine = RuleEngine([DummyRule(), FailingRule()])
    manifest = RepositoryManifest()
    context = RuleContext(manifest=manifest, repo_path=Path("/repo"))

    # FailingRule should not crash the engine, DummyRule should still report
    findings = await engine.run(context)
    assert len(findings) == 1
    assert findings[0].title == "Dummy"
