"""Application configuration loaded from environment variables via pydantic-settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single configuration object for the entire application.

    All values are read from environment variables (or .env file).
    This is the only place in the codebase that touches os.environ.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str

    # ── Redis ───────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Gemini ──────────────────────────────────────────────────────────────
    # Not used in M0; declared here so the config is complete from day one.
    gemini_api_key: str = ""
    gemini_model_fast: str = "gemini-2.0-flash"
    gemini_model_deep: str = "gemini-1.5-pro"

    # ── Clerk Authentication ────────────────────────────────────────────────
    clerk_secret_key: str = ""
    # Clerk instance-specific JWKS URL.
    # Default points to the global Clerk JWKS; override with your instance URL
    # (e.g. https://<your-clerk-domain>/.well-known/jwks.json) for production.
    clerk_jwks_url: str = "https://api.clerk.com/v1/jwks"

    # ── File Storage (local for MVP) ─────────────────────────────────────────
    report_output_dir: str = "./generated_reports"
    upload_temp_dir: str = "./tmp/uploads"

    # ── CORS ────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = ["http://localhost:3000"]

    # ── Application ─────────────────────────────────────────────────────────
    app_env: str = "development"
    app_version: str = "0.1.0"

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_asyncpg_driver(cls, v: str) -> str:
        """Normalise the database URL to always use the asyncpg driver.

        Accepts postgresql://, postgres://, or postgresql+asyncpg:// and
        ensures the result is always postgresql+asyncpg:// for SQLAlchemy.
        """
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


# Module-level singleton — import this everywhere instead of constructing Settings().
settings = Settings()
