"""Rule for detecting Cross Site Scripting (XSS) vulnerabilities."""

import re

from aegis.application.security.rules.base import RuleContext, SecurityRule
from aegis.domain.models.security import Confidence, Finding, Severity

# React dangerouslySetInnerHTML
REACT_DANGEROUS = re.compile(r"dangerouslySetInnerHTML\s*=\s*{", re.IGNORECASE)
# Jinja/Django unsafe filter
JINJA_SAFE = re.compile(r"{{.*\|\s*safe\s*}}", re.IGNORECASE)


class XSSRule(SecurityRule):
    """Detects unsafe HTML rendering and XSS vectors."""

    @property
    def rule_name(self) -> str:
        return "xss-detector"

    @property
    def target_languages(self) -> list[str]:
        return ["javascript", "typescript", "python"]

    async def analyze(self, context: RuleContext) -> list[Finding]:
        findings = []

        for file_node in context.get_files():
            content = file_node.content
            if not content:
                continue

            lines = content.splitlines()
            for idx, line in enumerate(lines):
                line_number = idx + 1

                # Check JS/TS for React dangerouslySetInnerHTML
                if file_node.path.endswith((".js", ".ts", ".jsx", ".tsx")):
                    if REACT_DANGEROUS.search(line):
                        findings.append(
                            self._create_finding(
                                file_node.path,
                                line_number,
                                line.strip(),
                                "React dangerouslySetInnerHTML Usage",
                                "Using dangerouslySetInnerHTML can expose the application to XSS attacks if the input is not sanitized.",
                            )
                        )

                # Check Python/HTML for Jinja/Django |safe filter
                if file_node.path.endswith((".py", ".html")):
                    if JINJA_SAFE.search(line):
                        findings.append(
                            self._create_finding(
                                file_node.path,
                                line_number,
                                line.strip(),
                                "Unsafe Template Rendering",
                                "Using the '|safe' filter in templates disables auto-escaping, which can lead to XSS if the rendered variable contains user input.",
                            )
                        )

        return findings

    def _create_finding(
        self, path: str, line_num: int, snippet: str, title: str, explanation: str
    ) -> Finding:
        return Finding(
            title=title,
            description="Potential Cross-Site Scripting (XSS) vector detected.",
            severity=Severity.HIGH,
            confidence=Confidence.TENTATIVE,
            cwe_id="CWE-79",
            owasp_category="A03:2021-Injection",
            file_path=path,
            line_start=line_num,
            line_end=line_num,
            code_snippet=snippet,
            explanation=explanation,
            remediation_recommendation="Ensure that any data rendered using this method is strictly sanitized (e.g., using DOMPurify for React) or validated. Prefer native secure rendering methods.",
        )
