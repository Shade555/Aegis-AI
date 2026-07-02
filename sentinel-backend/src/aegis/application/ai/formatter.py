"""Response formatting for AI outputs."""

import logging
from typing import Any

from aegis.domain.models.patch import AIPatchEnhancement
from aegis.domain.models.security import AIFindingEnhancement

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Safely formats and validates AI JSON responses into Pydantic models."""

    @staticmethod
    def parse_finding_enhancement(
        data: dict[str, Any],
    ) -> tuple[AIFindingEnhancement | None, int | None]:
        """Parses the finding response. Returns (enhancement, priority_score)."""
        try:
            enhancement = AIFindingEnhancement(
                explanation=str(data.get("explanation", "No explanation provided.")),
                impact=str(data.get("impact", "Unknown impact.")),
                severity_justification=str(
                    data.get("severity_justification", "No justification provided.")
                ),
                secure_coding_recommendation=str(
                    data.get("secure_coding_recommendation", "No recommendation.")
                ),
                best_practices=str(data.get("best_practices", "No best practices provided.")),
            )
            priority_score = data.get("priority_score")
            if priority_score is not None:
                priority_score = int(priority_score)
            return enhancement, priority_score
        except Exception as e:
            logger.error(f"Failed to parse AIFindingEnhancement: {e}")
            return None, None

    @staticmethod
    def parse_patch_enhancement(data: dict[str, Any]) -> AIPatchEnhancement | None:
        """Parses the patch response."""
        try:
            return AIPatchEnhancement(
                explanation=str(data.get("explanation", "No explanation provided.")),
                why_preferred=str(data.get("why_preferred", "Unknown preference.")),
                alternative_approaches=str(data.get("alternative_approaches", "None provided.")),
                possible_trade_offs=str(data.get("possible_trade_offs", "None provided.")),
            )
        except Exception as e:
            logger.error(f"Failed to parse AIPatchEnhancement: {e}")
            return None

    @staticmethod
    def parse_executive_summary(data: dict[str, Any]) -> dict[str, Any] | None:
        """Parses the executive summary response."""
        try:
            # We enforce standard fields just in case
            return {
                "overall_health": str(data.get("overall_health", "Analysis completed.")),
                "major_risks": list(data.get("major_risks", [])),
                "business_impact": str(
                    data.get("business_impact", "Business impact assessment unavailable.")
                ),
                "recommended_priorities": list(data.get("recommended_priorities", [])),
            }
        except Exception as e:
            logger.error(f"Failed to parse executive summary: {e}")
            return None
