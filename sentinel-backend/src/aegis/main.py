"""FastAPI application factory.

create_app() is the single entry point for constructing the application.
It is called once at module level to produce the `app` instance used by
uvicorn. This pattern makes the app fully testable — tests can call
create_app() with overrides rather than importing the module-level `app`.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException

from aegis.config import settings
from aegis.interface.api.exceptions import (
    AegisAPIError,
    aegis_exception_handler,
    http_exception_handler,
)
from aegis.interface.api.middleware.cors import configure_cors
from aegis.interface.api.routers import execution, health, projects


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Startup: Validate configuration, warm up connection pools.
    Shutdown: Cleanly close connection pools.
    """
    # Startup — nothing blocking in M0; connection pools are lazy.
    yield
    # Shutdown — SQLAlchemy engine disposal happens when the engine is GC'd,
    # but we can force it here in future milestones for graceful shutdown.


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    app = FastAPI(
        title="Aegis AI",
        description=(
            "An autonomous multi-agent AI security engineering platform. "
            "Audits software repositories, detects vulnerabilities, generates patches, "
            "and produces professional security reports."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware — applied in reverse order (last added is outermost).
    configure_cors(app)

    # Exception Handlers

    app.add_exception_handler(AegisAPIError, aegis_exception_handler)  # type: ignore
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore

    # Routers
    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(execution.router)

    return app


# Module-level app instance — used by uvicorn and imported by tests.
app = create_app()
