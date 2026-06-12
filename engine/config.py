"""
config.py — FORGE centralized settings (Phase 1)
Uses pydantic-settings. Import `settings` for typed access.
Module-level constants remain for backward compatibility with legacy imports.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # API security
    forge_api_key: str = Field(default="", alias="FORGE_API_KEY")
    forge_auth_enabled: bool = Field(default=True, alias="FORGE_AUTH_ENABLED")
    forge_api_port: int = Field(default=8000, alias="FORGE_API_PORT")
    forge_cors_origins: str = Field(
        default="http://localhost:3000,https://tradebuilt.io",
        alias="FORGE_CORS_ORIGINS",
    )

    # Flask platform (legacy)
    flask_secret_key: str = Field(default="", alias="FLASK_SECRET_KEY")
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")
    port: int = Field(default=8080, alias="PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Google Places
    google_places_api_key: str = Field(default="", alias="GOOGLE_PLACES_API_KEY")

    # Gmail outreach
    gmail_sender: str = Field(default="", alias="GMAIL_SENDER")
    gmail_app_password: str = Field(default="", alias="GMAIL_APP_PASSWORD")
    my_test_email: str = Field(default="", alias="MY_TEST_EMAIL")
    test_mode: bool = Field(default=True, alias="TEST_MODE")

    # Stripe
    stripe_secret_key: str = Field(default="sk_test_placeholder", alias="STRIPE_SECRET_KEY")
    stripe_publishable_key: str = Field(default="pk_test_placeholder", alias="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: str = Field(default="whsec_placeholder", alias="STRIPE_WEBHOOK_SECRET")

    # Optional integrations
    unsplash_access_key: str = Field(default="", alias="UNSPLASH_ACCESS_KEY")
    twilio_account_sid: str = Field(default="", alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", alias="TWILIO_AUTH_TOKEN")
    twilio_from: str = Field(default="", alias="TWILIO_FROM")
    my_phone: str = Field(default="", alias="MY_PHONE")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_username: str = Field(default="", alias="GITHUB_USERNAME")

    # Supabase
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")

    # Storage backend (Phase 2): csv | postgres
    storage_backend: str = Field(default="csv", alias="STORAGE_BACKEND")

    # Celery / Redis (Phase 3)
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="", alias="CELERY_RESULT_BACKEND")
    use_celery: bool = Field(default=True, alias="USE_CELERY")
    forge_role: str = Field(default="api", alias="FORGE_ROLE")  # api | worker | beat

    # Pipeline dashboard (deprecated)
    forge_dashboard_enabled: bool = Field(default=True, alias="FORGE_DASHBOARD_ENABLED")

    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url.strip() or self.redis_url

    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend.strip() or self.celery_broker

    @property
    def simulation_mode(self) -> bool:
        return self.stripe_secret_key.startswith("sk_test_placeholder")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.forge_cors_origins.split(",") if o.strip()]

    def require(self, *fields: str) -> None:
        """Raise ValueError if any named settings field is empty."""
        missing = [f for f in fields if not getattr(self, f, "")]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "See engine/.env.example"
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# ─── Backward-compatible module constants ─────────────────────────────────────

FLASK_SECRET_KEY: str = settings.flask_secret_key or "forge_dev_secret_change_me"
ADMIN_PASSWORD: str = settings.admin_password or "forge_admin"
PORT: int = settings.port
DEBUG: bool = settings.debug
GOOGLE_PLACES_API_KEY: str = settings.google_places_api_key
GMAIL_SENDER: str = settings.gmail_sender
GMAIL_APP_PASSWORD: str = settings.gmail_app_password
MY_TEST_EMAIL: str = settings.my_test_email
TEST_MODE: bool = settings.test_mode
STRIPE_SECRET_KEY: str = settings.stripe_secret_key
STRIPE_PUBLISHABLE_KEY: str = settings.stripe_publishable_key
STRIPE_WEBHOOK_SECRET: str = settings.stripe_webhook_secret
SIMULATION_MODE: bool = settings.simulation_mode
UNSPLASH_ACCESS_KEY: str = settings.unsplash_access_key
TWILIO_ACCOUNT_SID: str = settings.twilio_account_sid
TWILIO_AUTH_TOKEN: str = settings.twilio_auth_token
TWILIO_FROM: str = settings.twilio_from
MY_PHONE: str = settings.my_phone
ANTHROPIC_API_KEY: str = settings.anthropic_api_key
GITHUB_TOKEN: str = settings.github_token
GITHUB_USERNAME: str = settings.github_username