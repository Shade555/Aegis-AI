"""Rule for detecting SQL Injection vulnerabilities."""

import re

from aegis.application.security.rules.base import RuleContext, SecurityRule
from aegis.domain.models.security import Confidence, Finding, Severity

# Basic patterns for unsafe SQL concatenation/formatting
SQL_KEYWORDS = r"(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)"

PYTHON_F_STRING_SQL = re.compile(rf'f["\'].*{SQL_KEYWORDS}.*{{.*}}.*["\']', re.IGNORECASE)
PYTHON_FORMAT_SQL = re.compile(rf'["\'].*{SQL_KEYWORDS}.*["\']\.format\(', re.IGNORECASE)
PYTHON_PERCENT_SQL = re.compile(rf'["\'].*{SQL_KEYWORDS}.*%s.*["\']\s*%', re.IGNORECASE)

NODE_TEMPLATE_SQL = re.compile(rf"`.*{SQL_KEYWORDS}.*\${{.*}}.*`", re.IGNORECASE)
NODE_CONCAT_SQL = re.compile(rf'["\'].*{SQL_KEYWORDS}.*["\']\s*\+\s*[a-zA-Z_]', re.IGNORECASE)


class SqlInjectionRule(SecurityRule):
    """Detects unsafe SQL string concatenation and formatting."""

    @property
    def rule_name(self) -> str:
        return "sql-injection-detector"

    @property
    def target_languages(self) -> list[str]:
        return ["python", "javascript", "typescript"]

    async def analyze(self, context: RuleContext) -> list[Finding]:
        findings = []

        for file_node in context.get_files():
            # We only scan python and JS/TS files
            if not file_node.path.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                continue

            content = file_node.content
            if not content:
                continue

            lines = content.splitlines()
            for idx, line in enumerate(lines):
                line_number = idx + 1

                # Check Python patterns
                if file_node.path.endswith(".py"):
                    if (
                        PYTHON_F_STRING_SQL.search(line)
                        or PYTHON_FORMAT_SQL.search(line)
                        or PYTHON_PERCENT_SQL.search(line)
                    ):
                        findings.append(
                            self._create_finding(file_node.path, line_number, line.strip())
                        )

                # Check Node.js patterns
                if file_node.path.endswith((".js", ".ts", ".jsx", ".tsx")):
                    if NODE_TEMPLATE_SQL.search(line) or NODE_CONCAT_SQL.search(line):
                        findings.append(
                            self._create_finding(file_node.path, line_number, line.strip())
                        )

        return findings

    def _create_finding(self, path: str, line_num: int, snippet: str) -> Finding:
        return Finding(
            title="Potential SQL Injection",
            description="Unsafe SQL string formatting or concatenation detected. This can allow attackers to inject malicious SQL.",
            severity=Severity.HIGH,
            confidence=Confidence.TENTATIVE,
            cwe_id="CWE-89",
            owasp_category="A03:2021-Injection",
            file_path=path,
            line_start=line_num,
            line_end=line_num,
            code_snippet=snippet,
            explanation="Using f-strings, template literals, or string concatenation to build SQL queries is vulnerable to SQL injection if user input is included.",
            remediation_recommendation="Use parameterized queries (e.g., passing a tuple of arguments to cursor.execute) or an ORM like SQLAlchemy/Prisma instead of string formatting.",
        )
