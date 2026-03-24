from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    garmin_email: str = ""
    garmin_password: str = ""
    anthropic_api_key: str = ""
    polling_interval_seconds: int = 30
    database_path: str = "golf_coach.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
