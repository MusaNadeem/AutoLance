"""
AutoLance — Application Configuration
Pydantic Settings v2 with full type validation and env loading
"""
from functools import lru_cache
from typing import List, Optional
from pydantic import AnyHttpUrl, EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ─────────────────────────────────────────────
    APP_NAME: str = "AutoLance"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # ── Supabase ─────────────────────────────────────────
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "cv-documents"

    # ── Claude AI ────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""       # kept for backward compat — not used when AIML_API_KEY is set
    AIML_API_KEY: str = ""            # AI/ML API key (aimlapi.com) — takes priority when set
    AIML_BASE_URL: str = "https://api.aimlapi.com/v1"
    CLAUDE_MODEL: str = "anthropic/claude-sonnet-4-5"   # model name as used by AI/ML API
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.1

    # ── Bright Data ──────────────────────────────────────
    BRIGHT_DATA_API_KEY: Optional[str] = None
    BRIGHT_DATA_WS_ZONE: Optional[str] = None
    BRIGHT_DATA_UNLOCKER_ZONE: Optional[str] = None
    BRIGHT_DATA_USERNAME: Optional[str] = None
    BRIGHT_DATA_PASSWORD: Optional[str] = None
    BRIGHT_DATA_HOST: str = "brd.superproxy.io"
    BRIGHT_DATA_PORT: int = 22225
    BRIGHT_DATA_WS_DATASET_ID: Optional[str] = None

    # ── JWT ──────────────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Notification ─────────────────────────────────────────────────────────────
    SLACK_WEBHOOK_URL: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@autolance.io"
    SENDGRID_FROM_NAME: str = "AutoLance Alerts"
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REFRESH_TOKEN: Optional[str] = None
    GMAIL_SENDER_EMAIL: Optional[str] = None

    # ── Slack ────────────────────────────────────────────
    SLACK_DEFAULT_WEBHOOK_URL: Optional[str] = None

    # ── File Upload ──────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "/app/uploads"
    ALLOWED_UPLOAD_TYPES: str = (
        "application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "text/plain"
    )

    @property
    def allowed_upload_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_UPLOAD_TYPES.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Scraping ─────────────────────────────────────────
    SCRAPE_INTERVAL_MINUTES: int = 15
    SCRAPE_MAX_JOBS_PER_RUN: int = 500
    SCRAPE_RETRY_ATTEMPTS: int = 3
    SCRAPE_RETRY_DELAY_SECONDS: int = 30

    # ── Sentry ────────────────────────────────────────────
    SENTRY_DSN: Optional[str] = None

    # ── SMTP (all optional — app starts without them) ─────
    SMTP_HOST:       Optional[str] = None
    SMTP_PORT:       Optional[int] = None
    SMTP_USERNAME:   Optional[str] = None
    SMTP_PASSWORD:   Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    # ── Alert threshold default ───────────────────────────
    ALERT_THRESHOLD: float = 0.75

    # ── Scoring weights (must sum to 1.0) ─────────────────
    SCORE_WEIGHT_SKILL:           float = 0.35
    SCORE_WEIGHT_ROI:             float = 0.30
    SCORE_WEIGHT_COMPETITION:     float = 0.20
    SCORE_WEIGHT_CLIENT_QUALITY:  float = 0.15

    # Aliases used by scoring.py and tests
    @property
    def SCORE_WEIGHT_RELEVANCE(self) -> float:
        return self.SCORE_WEIGHT_SKILL

    @property
    def SCORE_WEIGHT_BUDGET(self) -> float:
        return self.SCORE_WEIGHT_ROI

    @model_validator(mode="after")
    def _validate_score_weights(self) -> "Settings":
        total = (
            self.SCORE_WEIGHT_SKILL
            + self.SCORE_WEIGHT_ROI
            + self.SCORE_WEIGHT_COMPETITION
            + self.SCORE_WEIGHT_CLIENT_QUALITY
        )
        if abs(total - 1.0) > 1e-5:
            raise ValueError(
                f"SCORE_WEIGHT_* values must sum to exactly 1.0, got {total:.6f}. "
                "Check your .env file."
            )
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
