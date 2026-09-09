from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "WhatsApp SaaS API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./whatsapp_saas.db"
    cors_origins: str = "http://localhost:3000"
    frontend_base_url: str = "http://localhost:3000"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    whatsapp_api_version: str = "v19.0"
    whatsapp_app_id: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_config_id: str = ""
    whatsapp_redirect_uri: str = ""
    whatsapp_scope: str = "whatsapp_business_messaging,whatsapp_business_management"
    whatsapp_webhook_verify_token: str = ""

    send_messages_per_minute: int = 60
    send_daily_limit: int = 1000
    send_rate_limit_backoff_seconds: int = 60
    send_max_backoffs: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()