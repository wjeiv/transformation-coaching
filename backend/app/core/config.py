import secrets
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Transformation Coaching"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://tc_user:tc_password@db:5432/transformation_coaching"
    DATABASE_URL_SYNC: str = "postgresql://tc_user:tc_password@db:5432/transformation_coaching"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Encryption key for Garmin credentials at rest
    GARMIN_ENCRYPTION_KEY: str = secrets.token_urlsafe(32)

    # First admin account
    FIRST_ADMIN_EMAIL: str = "admin@transformationcoaching.com"
    FIRST_ADMIN_PASSWORD: str = "changeme123!"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = "dev.env"
        case_sensitive = True


settings = Settings()
