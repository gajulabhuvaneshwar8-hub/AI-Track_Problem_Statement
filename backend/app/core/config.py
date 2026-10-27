"""
Application configuration — loaded from environment variables / .env file.
Secrets are NEVER hardcoded here.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Project metadata
    # ------------------------------------------------------------------
    PROJECT_NAME: str = "AI Payment Reconciliation Agent"
    PROJECT_VERSION: str = "0.1.0"
    PROJECT_DESCRIPTION: str = (
        "Automated financial reconciliation, anomaly detection and "
        "AI-powered exception management."
    )
    ENVIRONMENT: str = "development"

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/reconciliation_db"

    # ------------------------------------------------------------------
    # Security / Auth
    # ------------------------------------------------------------------
    JWT_SECRET: str = "changeme-use-a-strong-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ------------------------------------------------------------------
    # External AI service
    # ------------------------------------------------------------------
    AI_API_KEY: str = ""
    AI_SERVICE_URL: str = ""
    AI_TIMEOUT_SECONDS: int = 30
    AI_MODEL_NAME: str = "gemini-1.5-flash"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # alternative CRA/Next dev server
        "http://127.0.0.1:5173",
    ]


settings = Settings()
