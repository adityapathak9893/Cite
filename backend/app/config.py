import logging
from functools import lru_cache

from pydantic_settings import BaseSettings

# Single source of truth for the Claude model used by all services
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str
    openai_api_key: str
    anthropic_api_key: str
    cors_origins: str = "http://localhost:5173,https://cite.weaverbit.com,https://cite-omega.vercel.app"
    environment: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


def setup_logging() -> None:
    level = logging.INFO if get_settings().is_production else logging.DEBUG
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
