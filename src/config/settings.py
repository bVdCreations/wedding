from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    frontend_url: str = "http://localhost:4321"
    cors_origins: list[str] = ["*"]

    ENVIRONMENT: str = "Production"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wedding_rsvp"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/wedding_rsvp"

    # JWT
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Email (SMTP)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    emails_from: str = "info@gemma-bastiaan.wedding"

    # Email (Resend) - if set, use Resend API instead of SMTP
    resend_api_key: str = ""

    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.0

    RUN_MIGRATIONS_ON_STARTUP: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
