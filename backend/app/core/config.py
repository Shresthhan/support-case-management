from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Support Case Management API"
    app_version: str = "1.0.0"

    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/support_cases"
    )

    secret_key: str = "development-secret-change-this"

    access_token_expire_minutes: int = 60

    triage_provider: str = "mock"
    ai_api_key: str | None = None
    ai_api_base_url: str | None = None
    ai_model: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()