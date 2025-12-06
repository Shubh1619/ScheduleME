# backend/config.py

from functools import lru_cache
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    PROJECT_NAME: str = "SchedulMe API"
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: AnyUrl | str = "postgresql+psycopg2://user:password@localhost:5432/schedulme"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
