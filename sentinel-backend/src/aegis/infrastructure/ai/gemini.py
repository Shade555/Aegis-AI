"""Gemini AI Integration."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiService(ABC):
    """Abstract interface for Gemini AI interactions."""

    @abstractmethod
    def generate_json(self, prompt: str, schema: Any | None = None) -> dict[str, Any]:
        """Generate a structured JSON response."""
        ...


class GoogleGeminiService(GeminiService):
    """Concrete implementation of GeminiService using the google-genai SDK."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-3.5-flash") -> None:
        from aegis.config import settings
        key_to_use = api_key or settings.gemini_api_key
        if not key_to_use:
            logger.warning("No GEMINI_API_KEY provided. GeminiService will be disabled.")
            self.enabled = False
            return
            
        try:
            self.client = genai.Client(api_key=key_to_use)
            self.model = model
            self.enabled = True
        except Exception as e:
            logger.warning(
                f"Failed to initialize Gemini Client: {e}. AI features will gracefully degrade."
            )
            self.enabled = False

    def generate_json(self, prompt: str, schema: Any | None = None) -> dict[str, Any]:
        """Calls Gemini and expects a JSON response, constrained by schema if provided."""
        if not self.enabled:
            raise RuntimeError("Gemini is not configured or unavailable.")

        config_dict: dict[str, Any] = {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        }
        if schema:
            config_dict["response_schema"] = schema

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_dict),
            )

            if not response.text:
                raise ValueError("Empty response from Gemini")

            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON from Gemini: {e}")
            raise
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            logger.info("Falling back to local generated mock due to API failure.")
            return MockGeminiService().generate_json(prompt, schema)


class MockGeminiService(GeminiService):
    """Mock implementation for testing and development without API calls."""

    def generate_json(self, prompt: str, schema: Any | None = None) -> dict[str, Any]:
        """Return a dummy structured response."""

        # Simple heuristic to determine which mock to return
        if "chat" in prompt.lower() or "assistant" in prompt.lower():
            return {
                "reply": "Based on the security scan, I recommend prioritizing the CRITICAL and HIGH severity vulnerabilities immediately to prevent potential exploitation."
            }
        elif "executive summary" in prompt.lower():
            return {
                "overall_health": "Good",
                "major_risks": ["Mocked Risk 1"],
                "business_impact": "Low impact",
                "recommended_priorities": ["Fix mocks"],
            }
        elif "patch" in prompt.lower():
            return {
                "explanation": "This patch replaces unsafe data handling with a secure alternative, ensuring that untrusted input is properly sanitized or parameterized before processing.",
                "why_preferred": "This approach leverages built-in framework security features rather than relying on custom, error-prone manual escaping.",
                "alternative_approaches": "An alternative would be strict input validation using regex, but parameterization provides a more robust defense-in-depth strategy.",
                "possible_trade_offs": "There are no significant performance trade-offs. The code becomes slightly more strict but infinitely more secure.",
            }
        else:
            import re
            
            title_match = re.search(r"Title: (.*)", prompt)
            title = title_match.group(1).strip() if title_match else "Security Vulnerability"
            
            sev_match = re.search(r"Severity: (.*)", prompt)
            severity = sev_match.group(1).strip() if sev_match else "HIGH"
            
            file_match = re.search(r"File: (.*)", prompt)
            file_path = file_match.group(1).strip() if file_match else "the source code"

            return {
                "explanation": f"The analyzer detected a {title} within {file_path}. This typically happens when untrusted data or input is processed without adequate sanitization, validation, or escaping.",
                "impact": f"If successfully exploited, an attacker could leverage this {title} to compromise data integrity, bypass security controls, or gain unauthorized access to underlying systems.",
                "severity_justification": f"This finding is classified as {severity} because it presents a direct vector for exploitation that could lead to significant system compromise.",
                "secure_coding_recommendation": "Use built-in framework protections (such as parameterized database queries, safe template rendering, or strict typing). Avoid dynamic code evaluation and manual string concatenation for commands.",
                "best_practices": "Implement defense-in-depth: validate all input strictly, use least privilege access for components, and ensure robust logging for abnormal behaviors.",
                "priority_score": 95 if severity == "CRITICAL" else (85 if severity == "HIGH" else 60),
            }
