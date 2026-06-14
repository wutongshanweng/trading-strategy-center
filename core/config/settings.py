from pydantic_settings import BaseSettings
from typing import Literal, List, Optional
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

    initial_capital: float = 1_000_000.0  # 模拟账户初始资金
    max_position_size: int = 100
    max_drawdown_pct: float = 0.15
    max_leverage: float = 3.0

    cors_origins: List[str] = ["*"]

    # DeepSeek API Configuration
    deepseek_api_key: Optional[str] = None
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_tokens: int = 4096
    deepseek_temperature: float = 0.7

    # OpenAI API Configuration (for comparison)
    openai_api_key: Optional[str] = None
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    # Claude API Configuration (for comparison)
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-3-opus-20240229"

    # Default LLM provider
    default_llm_provider: Literal["deepseek", "openai", "claude"] = "deepseek"

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
