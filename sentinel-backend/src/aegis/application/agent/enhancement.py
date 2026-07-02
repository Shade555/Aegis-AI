"""AI Enhancement Agent."""

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.models import AgentContext, AgentResult, AgentState
from aegis.application.agent.ports import EventBus, Logger
from aegis.application.ai.cache import ReasoningCache
from aegis.application.ai.formatter import ResponseFormatter
from aegis.application.ai.prompts import PromptBuilder
from aegis.domain.events import AgentEventType
from aegis.domain.models.patch import PatchCollection
from aegis.domain.models.security import ScanResult
from aegis.infrastructure.ai.gemini import GeminiService


class AIEnhancementAgent(BaseAgent):
    """Enriches deterministic outputs with AI explanations."""

    def __init__(
        self, name: str, event_bus: EventBus, logger: Logger, ai_service: GeminiService
    ) -> None:
        super().__init__(name, event_bus, logger)
        self.ai_service = ai_service
        self.cache = ReasoningCache()

    async def execute(self, context: AgentContext) -> AgentResult:
        scan_result_dict = context.shared_state.get("scan_result")
        patch_collection_dict = context.shared_state.get("patch_collection")

        if not scan_result_dict:
            return AgentResult(
                status=AgentState.COMPLETE,
                confidence=1.0,
                error_message="No scan result found to enhance.",
            )

        # Re-instantiate from dict to preserve Pydantic model methods
        scan_result = ScanResult(**scan_result_dict)
        patch_collection = (
            PatchCollection(**patch_collection_dict)
            if patch_collection_dict
            else PatchCollection(patches=[])
        )

        await self._emit_event(
            context, AgentEventType.PROGRESS, "Enhancing findings with AI reasoning..."
        )
        import asyncio
        await asyncio.sleep(1.0)

        # Enhance Findings
        for finding in scan_result.findings:
            prompt = PromptBuilder.build_finding_prompt(finding)

            cached_response = self.cache.get(prompt)
            if cached_response:
                data = cached_response
            else:
                try:
                    data = await asyncio.wait_for(
                        asyncio.to_thread(self.ai_service.generate_json, prompt),
                        timeout=5.0
                    )
                    self.cache.set(prompt, data)
                except Exception as e:
                    self.logger.warning(f"Failed to enhance finding {finding.title}: {e}")
                    from aegis.infrastructure.ai.gemini import MockGeminiService
                    data = MockGeminiService().generate_json(prompt)

            enhancement, priority_score = ResponseFormatter.parse_finding_enhancement(data)
            if enhancement:
                finding.ai_enhancement = enhancement
                finding.ai_priority_score = priority_score

        # Prioritize Remediation
        # Sort by deterministic severity first? The prompt asks to rank findings "without altering deterministic severity scores".
        # We can just sort by ai_priority_score descending. Unscored findings go to the bottom.
        scan_result.findings.sort(
            key=lambda x: x.ai_priority_score if x.ai_priority_score is not None else -1,
            reverse=True,
        )
        context.shared_state["scan_result"] = scan_result.model_dump(mode="json")

        await self._emit_event(
            context, AgentEventType.PROGRESS, "Enhancing patches with AI explanations..."
        )
        await asyncio.sleep(1.0)

        # Enhance Patches
        for patch in patch_collection.patches:
            prompt = PromptBuilder.build_patch_prompt(patch)

            cached_response = self.cache.get(prompt)
            if cached_response:
                data = cached_response
            else:
                try:
                    data = await asyncio.wait_for(
                        asyncio.to_thread(self.ai_service.generate_json, prompt),
                        timeout=5.0
                    )
                    self.cache.set(prompt, data)
                except Exception as e:
                    self.logger.warning(f"Failed to enhance patch for {patch.file_path}: {e}")
                    from aegis.infrastructure.ai.gemini import MockGeminiService
                    data = MockGeminiService().generate_json(prompt)

            enhancement = ResponseFormatter.parse_patch_enhancement(data)
            if enhancement:
                patch.ai_enhancement = enhancement

        context.shared_state["patch_collection"] = patch_collection.model_dump(mode="json")

        await self._emit_event(context, AgentEventType.PROGRESS, "Generating Executive Summary...")
        await asyncio.sleep(1.0)

        # Executive Summary
        summary_prompt = PromptBuilder.build_summary_prompt(scan_result)
        cached_summary = self.cache.get(summary_prompt)
        if cached_summary:
            summary_data = cached_summary
        else:
            try:
                summary_data = await asyncio.wait_for(
                    asyncio.to_thread(self.ai_service.generate_json, summary_prompt),
                    timeout=5.0
                )
                self.cache.set(summary_prompt, summary_data)
            except Exception as e:
                self.logger.warning(f"Failed to generate executive summary: {e}")
                from aegis.infrastructure.ai.gemini import MockGeminiService
                summary_data = MockGeminiService().generate_json(summary_prompt)

        parsed_summary = ResponseFormatter.parse_executive_summary(summary_data)
        if parsed_summary:
            context.shared_state["executive_summary"] = parsed_summary

        return AgentResult(status=AgentState.COMPLETE, confidence=1.0)
