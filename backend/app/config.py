from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, loaded from environment variables / .env.

    Keeping all config in one typed object (instead of scattered os.getenv
    calls) pays off fast: you get autocomplete, validation at startup
    instead of at first use, and one place to see every external
    dependency the app has.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg2://nimbus:nimbus@localhost:5432/nimbus"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
