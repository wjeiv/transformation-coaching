import json
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
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    DATABASE_URL_SYNC: str = "sqlite:///./app.db"

    # CORS - Handle both string and list formats
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Handle CORS origins that might be passed as JSON string
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            try:
                self.BACKEND_CORS_ORIGINS = json.loads(self.BACKEND_CORS_ORIGINS)
            except (json.JSONDecodeError, TypeError):
                # Fallback to default if parsing fails
                self.BACKEND_CORS_ORIGINS = [
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
    FIRST_ADMIN_EMAIL: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "FFester1!"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Email configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "wjeiv4@gmail.com"
    SMTP_PASSWORD: str = "pitk kyyb mdsa xvez"
    CONTACT_EMAIL_TO: str = "transformation.coaching26.2@gmail.com"
    EMAIL_FROM: str = "noreply@transformationcoaching.com"

    class Config:
        env_file = "dev.env"
        case_sensitive = True


settings = Settings()
