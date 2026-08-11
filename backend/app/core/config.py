from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Support Case Management API"
    app_version: str = "1.0.0"

    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/support_cases"
    )

    secret_key: str = "development-secret-change-this"

    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()