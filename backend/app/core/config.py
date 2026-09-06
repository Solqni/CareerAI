from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，通过环境变量 / .env 注入。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 应用
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # 数据库（默认使用本地 SQLite，配置 DATABASE_URL 可切换到 PostgreSQL）
    DATABASE_URL: str = "sqlite+aiosqlite:///./careerai.db"

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
    DEEPSEEK_EMBEDDING_MODEL: str = "deepseek-embed"
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
