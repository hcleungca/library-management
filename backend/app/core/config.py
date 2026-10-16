import json
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the project root directory (4 levels up from config.py: core -> app -> backend -> repo root)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Check both the absolute project root path and relative .env in current working dir
        env_file=(
            str(PROJECT_ROOT / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Intelligent Library API"
    API_V1_STR: str = "/api"
    DEBUG: bool = True
    PORT: int = 8000

    # Database (Supabase PostgreSQL with pgvector)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/library_db"

    # Supabase Auth & Storage
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Anthropic Claude API (PydanticAI Agent)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-5-5"

    # CORS Allowed Origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Any) -> str:
        """Ensure standard postgresql connection strings use the psycopg2 dialect driver."""
        if isinstance(v, str):
            val = v.strip()
            if val.startswith("postgres://"):
                return val.replace("postgres://", "postgresql+psycopg2://", 1)
            if val.startswith("postgresql://") and not val.startswith("postgresql+"):
                return val.replace("postgresql://", "postgresql+psycopg2://", 1)
            return val
        return str(v)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        """Parse and normalize DEBUG into a boolean.

        Handles common string representations like 'release', 'prod', 'production' as False,
        and 'true', '1', 'debug', 'dev' as True.
        """
        if isinstance(v, str):
            val = v.strip().lower()
            if val in ("true", "1", "yes", "t", "debug", "dev", "development"):
                return True
            if val in ("false", "0", "no", "f", "release", "prod", "production"):
                return False
        return bool(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse and normalize CORS_ORIGINS into a list[str].

        Environment variables are injected into the application runtime as plain strings.
        Depending on the deployment target, CORS_ORIGINS may be formatted as:
          1. A JSON-encoded array string: '["http://localhost:5173", "http://localhost:3000"]'
             (standard in Docker Compose and .env files).
          2. A comma-separated string: 'http://localhost:5173, http://localhost:3000'
             (common in cloud environment variable dashboards like AWS Lightsail / Heroku).
          3. A native Python list[str] (when instantiated programmatically or using code defaults).

        This pre-validator normalizes all formats into a validated list[str], ensuring
        FastAPI's CORSMiddleware always receives clean, valid origin URLs without runtime crashes.
        """
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if item]
                except (json.JSONDecodeError, ValueError):
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(item).strip() for item in v if item]
        return []


settings = Settings()
