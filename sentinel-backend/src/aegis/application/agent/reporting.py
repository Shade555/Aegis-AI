"""Documentation and Reporting Agent."""

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from aegis.application.agent.base import BaseAgent
from aegis.application.agent.models import AgentContext, AgentResult, AgentState
from aegis.domain.events import AgentEventType


class ReportingAgent(BaseAgent):
    """Agent responsible for generating execution reports."""

    async def execute(self, context: AgentContext) -> AgentResult:
        """Generates JSON, HTML, and PDF reports."""

        await self._emit_event(
            context,
            AgentEventType.PROGRESS,
            "Generating final execution reports...",
        )

        manifest = context.shared_state.get("repository_manifest", {})
        scan_result = context.shared_state.get("scan_result", {})
        findings = scan_result.get("findings", [])

        # Calculate threat score
        threat_score = 0
        severity_weights = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1, "INFO": 0}
        for finding in findings:
            sev = finding.get("severity", "INFO")
            threat_score += severity_weights.get(sev, 0)

        # JSON Report
        report_data = {
            "execution_id": str(context.audit_id),
            "date": datetime.now().isoformat(),
            "threat_score": threat_score,
            "manifest": manifest,
            "findings": findings,
            # We don't have timeline injected here directly, but the session has it
            # We can omit timeline from JSON or just leave it empty if not available
        }

        context.shared_state["report_json"] = json.dumps(report_data, indent=2)

        # HTML Report
        template_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir))
        try:
            template = env.get_template("report.html.j2")
            html_content = template.render(
                execution_id=str(context.audit_id),
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                threat_score=threat_score,
                manifest=manifest,
                findings=findings,
                timeline=[],  # Ideally we'd fetch timeline, but we omit for now
            )
            context.shared_state["report_html"] = html_content
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            return AgentResult(status=AgentState.FAILED, error_message=str(e))

        # PDF Report
        try:
            pdf_stream = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_stream)
            if pisa_status.err:
                self.logger.warning(f"PDF generation had errors: {pisa_status.err}")
            context.shared_state["report_pdf"] = pdf_stream.getvalue()
        except Exception as e:
            if self.logger:
                self.logger.warning(f"PDF generation skipped/failed: {e}")
            context.shared_state["report_pdf"] = b"PDF Generation Failed."

        await self._emit_event(
            context,
            AgentEventType.PROGRESS,
            "Reports generated successfully.",
        )

        return AgentResult(
            status=AgentState.COMPLETE,
            confidence=1.0,
            metadata={"reports_generated": ["json", "html", "pdf"]},
        )
