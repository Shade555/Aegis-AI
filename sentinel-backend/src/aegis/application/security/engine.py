"""The Security Analysis Rule Engine."""

import asyncio
import logging

from aegis.application.security.rules.base import RuleContext, SecurityRule
from aegis.domain.models.security import Finding

logger = logging.getLogger(__name__)


class RuleEngine:
    """Executes a suite of security rules against a repository manifest."""

    def __init__(self, rules: list[SecurityRule]):
        self.rules = rules

    async def run(self, context: RuleContext) -> list[Finding]:
        """Runs all applicable rules concurrently.

        Args:
            context: The context containing the repository manifest.

        Returns:
            A consolidated list of all Findings.
        """
        if not self.rules:
            return []

        # We can run rules concurrently since they do static analysis on the same manifest
        tasks = []
        for rule in self.rules:
            # We could filter by target_languages here if we want to optimize,
            # but for now we let the rules decide internally based on file extensions.
            tasks.append(self._run_rule_safe(rule, context))

        results = await asyncio.gather(*tasks)

        # Flatten the list of lists
        all_findings = []
        for findings in results:
            all_findings.extend(findings)

        return all_findings

    async def _run_rule_safe(self, rule: SecurityRule, context: RuleContext) -> list[Finding]:
        """Runs a single rule and catches any unhandled exceptions."""
        try:
            return await rule.analyze(context)
        except Exception as e:
            logger.error(f"Rule {rule.rule_name} failed: {e}")
            return []
