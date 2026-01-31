from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    frontend_url: str = "http://localhost:4321"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wedding_rsvp"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/wedding_rsvp"

    # JWT
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Email
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    emails_from: str = "wedding@example.com"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
