"""Rule for detecting vulnerable dependencies via manifest parsing."""

import json
import re

from aegis.application.security.rules.base import RuleContext, SecurityRule
from aegis.domain.models.security import Confidence, Finding, Severity

# Mock local CVE database
KNOWN_VULNERABLE = {
    "npm": {
        "lodash": ["4.17.15", "4.17.19"],  # Prototype pollution
        "axios": ["0.21.0", "0.21.1"],  # SSRF
    },
    "pip": {
        "django": ["3.1.0", "3.1.1", "3.1.2"],  # Potential bypass
        "requests": ["2.25.0"],
    },
}


class DependenciesRule(SecurityRule):
    """Scans package.json and requirements.txt for known vulnerable versions."""

    @property
    def rule_name(self) -> str:
        return "vulnerable-dependencies-detector"

    @property
    def target_languages(self) -> list[str]:
        return ["python", "javascript"]

    async def analyze(self, context: RuleContext) -> list[Finding]:
        findings = []

        for file_node in context.get_files():
            content = file_node.content
            if not content:
                continue

            if file_node.path.endswith("package.json"):
                findings.extend(self._analyze_package_json(file_node.path, content))

            elif file_node.path.endswith("requirements.txt"):
                findings.extend(self._analyze_requirements_txt(file_node.path, content))

        return findings

    def _analyze_package_json(self, path: str, content: str) -> list[Finding]:
        findings = []
        try:
            data = json.loads(content)
            deps = data.get("dependencies", {})
            deps.update(data.get("devDependencies", {}))

            for pkg, version in deps.items():
                # Strip semantic versioning chars for exact match in our dummy db
                clean_version = re.sub(r"[\^~>=<]", "", version).strip()
                if pkg in KNOWN_VULNERABLE["npm"] and clean_version in KNOWN_VULNERABLE["npm"][pkg]:
                    findings.append(
                        self._create_finding(
                            path=path,
                            pkg_manager="npm",
                            pkg_name=pkg,
                            version=clean_version,
                            snippet=f'"{pkg}": "{version}"',
                        )
                    )
        except json.JSONDecodeError:
            pass
        return findings

    def _analyze_requirements_txt(self, path: str, content: str) -> list[Finding]:
        findings = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            # Parse 'django==3.1.0'
            match = re.match(r"^([a-zA-Z0-9\-_]+)==([0-9\.]+)", line.strip())
            if match:
                pkg = match.group(1).lower()
                version = match.group(2)
                if pkg in KNOWN_VULNERABLE["pip"] and version in KNOWN_VULNERABLE["pip"][pkg]:
                    findings.append(
                        self._create_finding(
                            path=path,
                            pkg_manager="pip",
                            pkg_name=pkg,
                            version=version,
                            snippet=line.strip(),
                            line_num=idx + 1,
                        )
                    )
        return findings

    def _create_finding(
        self,
        path: str,
        pkg_manager: str,
        pkg_name: str,
        version: str,
        snippet: str,
        line_num: int = 1,
    ) -> Finding:
        return Finding(
            title=f"Vulnerable Dependency: {pkg_name} ({version})",
            description=f"The {pkg_manager} package '{pkg_name}' at version '{version}' is known to contain vulnerabilities.",
            severity=Severity.HIGH,
            confidence=Confidence.CERTAIN,
            cwe_id="CWE-1104",
            owasp_category="A06:2021-Vulnerable and Outdated Components",
            file_path=path,
            line_start=line_num,
            line_end=line_num,
            code_snippet=snippet,
            explanation=f"A publicly disclosed vulnerability affects {pkg_name} {version}. Using vulnerable components exposes the application to known attack vectors.",
            remediation_recommendation=f"Update {pkg_name} to the latest secure version.",
        )
