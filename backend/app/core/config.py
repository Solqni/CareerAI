import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """应用配置，通过环境变量 / .env 注入。"""

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    # 应用
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # 数据库
    DATABASE_TYPE: str = "postgresql"  # postgresql | sqlite
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "careerai"
    POSTGRES_PASSWORD: str = "careerai_password"
    POSTGRES_DB: str = "careerai"

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_TYPE == "sqlite":
            return "sqlite+aiosqlite:///careerai.db"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # LLM (DeepSeek)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_CHAT_MODEL: str = "deepseek-chat"
    # 视觉模型（用于识别 JD 截图等图片输入，走同一 OpenAI 兼容端点）
    DEEPSEEK_VISION_MODEL: str = "qwen-vl-plus"
    DEEPSEEK_EMBEDDING_MODEL: str = "text-embedding-v3"
    EMBEDDING_DIMENSIONS: int = 1024
    LLM_TEMPERATURE: float = 0.3
    LLM_TIMEOUT: int = 60

    # RAG
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 80
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.5


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
