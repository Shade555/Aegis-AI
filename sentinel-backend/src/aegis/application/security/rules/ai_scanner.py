"""AI-Powered Security Scanning Rule."""

import logging
import os
from typing import Any

from aegis.application.security.rules.base import RuleContext, SecurityRule
from aegis.domain.models.security import Finding, Severity
from aegis.infrastructure.ai.gemini import GeminiService

logger = logging.getLogger(__name__)

# Extensions that are mostly safe to pass to LLM (no binaries)
SUPPORTED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".c", ".cpp", ".h", ".rs", ".php", ".rb"
}

# The expected JSON schema for the Gemini response
FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {"type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]},
                    "file_path": {"type": "string"},
                    "line_start": {"type": "integer"},
                    "line_end": {"type": "integer"},
                    "code_snippet": {"type": "string"},
                    "explanation": {"type": "string"},
                    "remediation_recommendation": {"type": "string"}
                },
                "required": [
                    "title", "description", "severity", "file_path", 
                    "line_start", "line_end", "code_snippet", "explanation", "remediation_recommendation"
                ]
            }
        }
    },
    "required": ["findings"]
}

class AiSecurityRule(SecurityRule):
    """Uses an LLM to scan for complex vulnerabilities like SSRF, Path Traversal, Command Injection."""
    
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.rule_id = "AI_VULN_SCANNER"
        self.description = "Uses GenAI to detect complex, diverse threats."

    @property
    def rule_name(self) -> str:
        return "AI-Driven Vulnerability Detection"

    @property
    def target_languages(self) -> list[str]:
        return [] # All languages

    async def analyze(self, context: RuleContext) -> list[Finding]:
        """Bundles source code and passes it to the Gemini service."""
        
        if not getattr(self.gemini_service, "enabled", True):
            # If GoogleGeminiService is used but no API key was provided, it's disabled.
            # Avoid sending code if it's going to fail.
            logger.info("Skipping AI Security Rule because Gemini is disabled.")
            return []

        # 1. Gather all relevant source files
        files_content = []
        token_estimate = 0
        MAX_TOKENS = 800000 # Keep well within Gemini 2.5 Flash's 1M context limit
        
        for file_path in context.repo_path.rglob("*"):
            if not file_path.is_file():
                continue
                
            # Skip hidden dirs like .git or node_modules
            if any(part.startswith(".") or part == "node_modules" for part in file_path.parts):
                continue
                
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
                
            try:
                content = file_path.read_text(encoding="utf-8")
                # Very rough token estimate (chars / 4)
                est_tokens = len(content) // 4
                
                if token_estimate + est_tokens > MAX_TOKENS:
                    logger.warning("Reached token limit for AI scanner, truncating file context.")
                    break
                    
                rel_path = file_path.relative_to(context.repo_path).as_posix()
                files_content.append(f"--- FILE: {rel_path} ---\n{content}\n")
                token_estimate += est_tokens
                
            except Exception:
                continue
                
        if not files_content:
            return []
            
        combined_code = "\n".join(files_content)
        
        # 2. Build the Prompt
        prompt = f"""
You are an expert cybersecurity auditor. Review the following application source code and identify any security vulnerabilities.
Look specifically for complex logic flaws such as:
- OS Command Injection (CWE-78)
- Path Traversal / Arbitrary File Read (CWE-22)
- Server-Side Request Forgery (SSRF) (CWE-918)
- Code Injection / Eval (CWE-94)
- Cross-Site Scripting (XSS) (CWE-79)
- SQL Injection (CWE-89)

Return your findings in the exact JSON schema requested.
If no vulnerabilities are found, return an empty "findings" array.

SOURCE CODE:
{combined_code}
"""
        
        # 3. Call the AI
        try:
            response = self.gemini_service.generate_json(prompt, schema=FINDINGS_SCHEMA)
            raw_findings = response.get("findings", [])
            
            findings = []
            for f in raw_findings:
                # Map string severity to Enum
                sev_str = f.get("severity", "MEDIUM")
                severity = getattr(Severity, sev_str, Severity.MEDIUM)
                
                finding = Finding(
                    rule_id=self.rule_id,
                    title=f.get("title", "AI Detected Vulnerability"),
                    description=f.get("description", ""),
                    severity=severity,
                    file_path=f.get("file_path", "unknown"),
                    line_start=f.get("line_start", 1),
                    line_end=f.get("line_end", 1),
                    code_snippet=f.get("code_snippet", ""),
                    explanation=f.get("explanation", ""),
                    remediation_recommendation=f.get("remediation_recommendation", ""),
                    confidence="CERTAIN" if severity in (Severity.CRITICAL, Severity.HIGH) else "TENTATIVE"
                )
                
                # Automatically mark it as AI enhanced since the AI found it!
                from aegis.domain.models.security import AIEnhancement
                finding.ai_enhancement = AIEnhancement(
                    explanation=finding.explanation,
                    impact=finding.description,
                    severity_justification=f"AI assigned severity {severity.value} based on context.",
                    secure_coding_recommendation=finding.remediation_recommendation,
                    best_practices="Always validate user input and avoid dangerous functions.",
                    priority_score=100 if severity == Severity.CRITICAL else 80
                )
                
                findings.append(finding)
                
            return findings
            
        except Exception as e:
            logger.error(f"AI Scanner failed: {e}")
            return []
