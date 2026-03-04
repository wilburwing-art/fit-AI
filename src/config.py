"""Application configuration"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./fit_agent.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False

    # Security
    secret_key: str = "insecure-secret-key-change-in-production"

    # AI Providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # AI Model Selection (override via env vars)
    planning_model: str = "anthropic:claude-opus-4-1-20250805"
    analysis_model: str = "anthropic:claude-sonnet-4-5-20250929"
    coaching_model: str = "anthropic:claude-sonnet-4-5-20250929"
    validation_model: str = "anthropic:claude-haiku-4-5-20251001"
    extraction_model: str = "openai:gpt-4o-mini"
    long_context_model: str = "google-gla:gemini-2.5-pro"

    # Observability
    logfire_token: str = ""

    # App Settings
    environment: str = "development"
    debug: bool = True

    # Email (optional)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""


settings = Settings()
