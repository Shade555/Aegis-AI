"""FastAPI Dependencies."""

from aegis.application.execution.manager import session_manager
from aegis.application.services.analysis import AnalysisService

# We instantiate the service once for now to keep the MVP simple.
# In a real app with DB, we might instantiate it per request if it relies on a DB session.
_analysis_service = AnalysisService(session_manager=session_manager)


def get_analysis_service() -> AnalysisService:
    """Dependency injection provider for AnalysisService."""
    return _analysis_service
