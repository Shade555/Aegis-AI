"""Rule for detecting hardcoded secrets."""

import re

from aegis.application.security.rules.base import RuleContext, SecurityRule
from aegis.domain.models.security import Confidence, Finding, Severity

# Curated high-fidelity patterns
SECRET_PATTERNS = {
    "AWS Access Key": re.compile(r"(?<![A-Z0-9])[A][K][I][A][A-Z0-9]{16}(?![A-Z0-9])"),
    "Stripe Secret Key": re.compile(r"sk_(live|test)_[0-9a-zA-Z]{24}"),
    "Google API Key": re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    "RSA Private Key": re.compile(r"-----BEGIN RSA PRIVATE KEY-----"),
    "GitHub Personal Access Token": re.compile(r"ghp_[0-9a-zA-Z]{36}"),
}


class SecretsRule(SecurityRule):
    """Detects hardcoded secrets, API keys, and tokens."""

    @property
    def rule_name(self) -> str:
        return "hardcoded-secrets-detector"

    @property
    def target_languages(self) -> list[str]:
        return ["*"]  # Applies to all files

    async def analyze(self, context: RuleContext) -> list[Finding]:
        findings = []

        for file_node in context.get_files():
            # Skip binary or lock files
            if file_node.path.endswith((".lock", ".pyc", ".png", ".jpg", ".pdf")):
                continue

            content = file_node.content
            if not content:
                continue

            lines = content.splitlines()
            for idx, line in enumerate(lines):
                line_number = idx + 1

                for secret_type, pattern in SECRET_PATTERNS.items():
                    if pattern.search(line):
                        findings.append(
                            self._create_finding(
                                secret_type, file_node.path, line_number, line.strip()
                            )
                        )

        return findings

    def _create_finding(self, secret_type: str, path: str, line_num: int, snippet: str) -> Finding:
        # We obscure the actual secret in the snippet for safety in the report
        obscured_snippet = snippet
        if len(snippet) > 10:
            obscured_snippet = snippet[:10] + "..." + snippet[-5:]

        return Finding(
            title=f"Hardcoded {secret_type}",
            description=f"A hardcoded {secret_type} was found in the source code.",
            severity=Severity.CRITICAL,
            confidence=Confidence.CERTAIN,
            cwe_id="CWE-798",
            owasp_category="A07:2021-Identification and Authentication Failures",
            file_path=path,
            line_start=line_num,
            line_end=line_num,
            code_snippet=obscured_snippet,
            explanation="Storing secrets directly in source code allows anyone with read access to the repository to impersonate the application or access sensitive external systems.",
            remediation_recommendation="Remove the secret from the source code. Rotate the compromised key immediately. Use environment variables or a secret management service (e.g., AWS Secrets Manager, HashiCorp Vault) to inject secrets at runtime.",
        )
