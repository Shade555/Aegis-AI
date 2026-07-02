"""CORS configuration helper.

Exports configure_cors() to keep CORS setup out of main.py and
make the allowed origins testable in isolation.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aegis.config import settings


def configure_cors(app: FastAPI) -> None:
    """Attach CORSMiddleware to the FastAPI application.

    Allowed origins are read from settings.allowed_origins so they
    can be set per-environment via the ALLOWED_ORIGINS env variable.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
