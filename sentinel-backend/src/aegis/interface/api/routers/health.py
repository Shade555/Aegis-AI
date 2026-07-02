"""Health check endpoint."""

import time
from typing import Any

from fastapi import APIRouter

from aegis.config import settings

router = APIRouter()
START_TIME = time.monotonic()


@router.get(
    "/health",
    summary="Health check",
    description="Returns operational status of the API.",
    tags=["health"],
)
async def health_check() -> dict[str, Any]:
    """Check the health of the service."""
    uptime_seconds = int(time.monotonic() - START_TIME)

    return {
        "status": "ok",
        "version": settings.app_version,
        "env": settings.app_env,
        "uptime_seconds": uptime_seconds,
    }
