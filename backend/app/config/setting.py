"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """SchedulMe configuration class."""

    # Database
    database_url: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Fernet Encryption Key
    fernet_key: str

    # Meta OAuth (Phase 1)
    meta_client_id: str
    meta_client_secret: str
    meta_redirect_uri: str
    meta_scopes: str


    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
