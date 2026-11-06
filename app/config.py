from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project Info
    PROJECT_NAME: str = "AuditFlow AI"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Databases (Async for FastAPI, Sync for Celery / Alembic)
    POSTGRES_USER: str = "auditflow"
    POSTGRES_PASSWORD: str = "change_me"
    POSTGRES_DB: str = "auditflow"
    DATABASE_URL: str = "postgresql+asyncpg://auditflow:change_me@localhost:5432/auditflow"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://auditflow:change_me@localhost:5432/auditflow"

    # Redis Queue
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & JWT
    JWT_SECRET: str = "change_me_to_a_long_random_string_at_least_32_chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # LLM Settings
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_API_KEY: str = "mock_key"
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    # Vector Embeddings
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_API_KEY: str = "mock_key"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 10
    RATE_LIMIT_PER_MINUTE: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()

