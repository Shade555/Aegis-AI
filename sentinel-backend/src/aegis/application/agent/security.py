"""Security Analysis Agent Implementation."""

from pathlib import Path
from typing import Any

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.models import AgentContext, AgentResult, AgentState
from aegis.application.agent.repository import RepositoryManifest
from aegis.application.security.engine import RuleEngine
from aegis.application.security.rules.base import RuleContext
from aegis.application.security.rules.dependencies import DependenciesRule
from aegis.application.security.rules.secrets import SecretsRule
from aegis.application.security.rules.sql_injection import SqlInjectionRule
from aegis.application.security.rules.xss import XSSRule
from aegis.domain.events import AgentEventType
from aegis.domain.models.security import ScanResult


def get_default_rules(gemini_service: Any = None) -> list[Any]:
    """Returns the default set of security rules."""
    rules = [
        SqlInjectionRule(),
        SecretsRule(),
        XSSRule(),
        DependenciesRule(),
    ]
    
    if gemini_service:
        from aegis.application.security.rules.ai_scanner import AiSecurityRule
        rules.append(AiSecurityRule(gemini_service))
        
    return rules


class SecurityAnalysisAgent(BaseAgent):
    """Agent responsible for performing static security analysis."""

    def __init__(self, agent_id: str, event_bus: Any, logger: Any, rules: list[Any] | None = None, gemini_service: Any = None):
        super().__init__(agent_id, event_bus, logger)
        self.rules = rules or get_default_rules(gemini_service)
        self.engine = RuleEngine(self.rules)

    async def execute(self, context: AgentContext) -> AgentResult:
        """Executes the security scan using the repository manifest."""
        manifest_data = context.shared_state.get("repository_manifest")
        repo_path_str = context.shared_state.get("repo_path")

        if not manifest_data or not repo_path_str:
            self.logger.error("Repository manifest or repo_path not found in shared state.")
            return AgentResult(
                status=AgentState.FAILED,
                metadata={"error": "Missing repository_manifest or repo_path"},
            )

        repo_path = Path(repo_path_str)

        # Deserialize the manifest if it's a dict (expected if serialized to state)
        if isinstance(manifest_data, dict):
            manifest = RepositoryManifest.model_validate(manifest_data)
        elif isinstance(manifest_data, RepositoryManifest):
            manifest = manifest_data
        else:
            self.logger.error("Invalid repository manifest format.")
            return AgentResult(
                status=AgentState.FAILED, metadata={"error": "Invalid manifest format"}
            )

        await self._emit_event(
            context,
            AgentEventType.SECURITY_SCAN_STARTED,
            "Starting security analysis scan...",
            {"rule_count": len(self.rules)},
        )

        rule_context = RuleContext(manifest=manifest, repo_path=repo_path)

        # We manually emit rule events here instead of inside the engine to keep the engine decoupled from the agent event bus
        all_findings = []
        for rule in self.rules:
            await self._emit_event(
                context,
                AgentEventType.RULE_STARTED,
                f"Running rule: {rule.rule_name}",
                {"rule_name": rule.rule_name},
            )
            import asyncio
            await asyncio.sleep(1.5)

            try:
                findings = await rule.analyze(rule_context)
                all_findings.extend(findings)

                for finding in findings:
                    await self._emit_event(
                        context,
                        AgentEventType.FINDING_DETECTED,
                        f"Finding detected: {finding.title}",
                        {
                            "finding_id": str(finding.id),
                            "rule_name": rule.rule_name,
                            "severity": finding.severity.value,
                        },
                    )

                await self._emit_event(
                    context,
                    AgentEventType.RULE_COMPLETED,
                    f"Rule {rule.rule_name} completed with {len(findings)} findings.",
                    {"rule_name": rule.rule_name, "findings_count": len(findings)},
                )
            except Exception as e:
                self.logger.error(f"Rule {rule.rule_name} failed: {str(e)}")

        scan_result = ScanResult(audit_id=context.audit_id, findings=all_findings)

        context.shared_state["scan_result"] = scan_result.model_dump(mode="json")

        await self._emit_event(
            context,
            AgentEventType.SECURITY_SCAN_COMPLETED,
            f"Security scan completed. Total findings: {len(all_findings)}.",
            {"total_findings": len(all_findings), "summary": scan_result.get_summary_stats()},
        )

        return AgentResult(
            status=AgentState.COMPLETE,
            metadata={
                "total_findings": len(all_findings),
                "summary": scan_result.get_summary_stats(),
            },
        )
