from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "MatchHire AI"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., min_length=32)

    # ── CORS ─────────────────────────────────────────────
    ALLOWED_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list) -> list:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = Field(..., pattern=r"^postgresql(\+asyncpg)?://")

    # ── Supabase ─────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # ── Storage ──────────────────────────────────────────
    SUPABASE_STORAGE_BUCKET: str = "resumes"

    # ── File upload constraints ───────────────────────────
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
        {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    )
    ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx"})

    # ── AI / External APIs ───────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    AFFINDA_API_KEY: str = ""

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Celery ───────────────────────────────────────────
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton — safe to call anywhere."""
    return Settings()
