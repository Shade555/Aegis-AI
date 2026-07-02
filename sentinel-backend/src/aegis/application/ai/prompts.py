"""Prompt Builder for AI interactions."""

from aegis.domain.models.patch import Patch
from aegis.domain.models.security import Finding, ScanResult


class PromptBuilder:
    """Builds strict prompt templates for Gemini."""

    @staticmethod
    def build_finding_prompt(finding: Finding) -> str:
        return f"""
You are a senior Application Security Engineer.
Please analyze the following security vulnerability detected in a codebase.
DO NOT invent new findings. DO NOT change the deterministic severity. Enqueue your response as JSON.

Vulnerability Context:
Title: {finding.title}
Severity: {finding.severity.value}
File: {finding.file_path}
Code Snippet:
```
{finding.code_snippet}
```
Deterministic Explanation: {finding.explanation}

Provide a JSON response with exactly these keys:
- "explanation": An in-depth, human-readable explanation of this specific vulnerability.
- "impact": Real-world consequences if exploited.
- "severity_justification": Why this aligns with {finding.severity.value} severity.
- "secure_coding_recommendation": How to fix it (general advice).
- "best_practices": Relevant industry best practices to prevent recurrence.
- "priority_score": A score from 0-100 to rank this finding among others, considering impact and exploitability.
"""

    @staticmethod
    def build_patch_prompt(patch: Patch) -> str:
        return f"""
You are a senior Application Security Engineer.
Please analyze the following proposed patch for a security vulnerability.
DO NOT invent a new patch. DO NOT modify the existing patch. Output JSON only.

Context:
File: {patch.file_path}
Original Code:
```
{patch.original_snippet}
```
Patched Code:
```
{patch.patched_snippet}
```
Deterministic Reason: {patch.explanation.problem} -> {patch.explanation.solution}

Provide a JSON response with exactly these keys:
- "explanation": An AI explanation of how the patched code works.
- "why_preferred": Why this fix strategy is preferred over other naive fixes.
- "alternative_approaches": Other ways one might fix it (and why they might be worse).
- "possible_trade_offs": Any performance or compatibility trade-offs introduced by this patch.
"""

    @staticmethod
    def build_summary_prompt(scan_result: ScanResult) -> str:
        findings_summary = []
        for f in scan_result.findings:
            findings_summary.append(f"- {f.severity.value}: {f.title} in {f.file_path}")

        return f"""
You are the CISO's executive assistant generating an AI summary of a recent automated security audit.
Analyze the following list of findings and provide an executive-level summary in JSON format.

Findings:
{chr(10).join(findings_summary) if findings_summary else "No vulnerabilities found."}

Provide a JSON response with exactly these keys:
- "overall_health": A brief 1-sentence summary of the repository's security posture.
- "major_risks": An array of strings describing the biggest risks discovered.
- "business_impact": A paragraph explaining the potential business impact.
- "recommended_priorities": An array of strings with high-level steps to remediate.
"""

    @staticmethod
    def build_chat_prompt(query: str, findings: list[Finding], patches: list[Patch]) -> str:
        context = "Context regarding the current analysis:\n"
        for f in findings:
            context += f"Finding: {f.title} ({f.severity.value}) in {f.file_path}\n"
        for p in patches:
            context += f"Patch for {p.file_path}: {p.explanation.solution}\n"

        return f"""
You are the Aegis AI Assistant. You answer questions strictly based on the current repository analysis context below.
DO NOT provide arbitrary answers. If the question is unrelated to the context, politely decline.

{context}

User Query: {query}

Provide a JSON response with exactly one key:
- "reply": Your detailed markdown-formatted response to the user.
"""
