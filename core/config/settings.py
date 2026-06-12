from pydantic_settings import BaseSettings
from typing import Literal, List
from functools import lru_cache


class Settings(BaseSettings):
    env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key"

    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "trading"
    db_pass: str = "trading_pass"
    db_name: str = "trading_strategy_center"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    lru_cache_size: int = 1000
    redis_cache_ttl: int = 300

    max_position_size: int = 100
    max_drawdown_pct: float = 0.15
    max_leverage: float = 3.0

    cors_origins: List[str] = ["*"]

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
