"""API Custom Exceptions."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AegisAPIError(Exception):
    """Base class for Aegis API exceptions."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AnalysisNotFoundError(AegisAPIError):
    """Raised when an execution session is not found."""

    def __init__(self, execution_id: str):
        super().__init__(status_code=404, detail=f"Execution {execution_id} not found.")


class InvalidProjectStateError(AegisAPIError):
    """Raised when an operation is performed in an invalid project state."""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


async def aegis_exception_handler(request: Request, exc: AegisAPIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.__class__.__name__, "message": exc.detail}},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTPException", "message": exc.detail}},
    )
