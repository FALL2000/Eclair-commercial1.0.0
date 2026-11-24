from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Base de données PostgreSQL ---
    db_user: str = "eclair"
    db_password: str = "eclair"
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "eclair_commercial"
    db_engine_string: str = "postgresql+psycopg"
    db_echo: bool = False

    # --- API ---
    api_prefix: str = "/api/v1"
    origins_cors: str = ""
    host_ip: str = "127.0.0.1"
    app_env: str = "dev"
    debug: bool = False

    # --- Sécurité JWT ---
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    access_refresh_token_expire_days: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        return (
            f"{self.db_engine_string}://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def origins(self) -> List[str]:
        if not self.origins_cors:
            return ["*"]
        return [origin.strip() for origin in self.origins_cors.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
