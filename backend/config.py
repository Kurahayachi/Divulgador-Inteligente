from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SmartDeals Bot"
    secret_key: str = "change-me"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    access_token_expire_minutes: int = 480

    db_path: str = "data/smartdeals.db"
    logs_path: str = "data/smartdeals.log"

    scheduler_interval_minutes: int = 20
    request_timeout_seconds: int = 15


settings = Settings()