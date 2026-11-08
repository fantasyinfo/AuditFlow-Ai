import os
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

    # LLM Settings (Defaults to Google AI Studio Gemini API)
    LLM_PROVIDER: str = "google"
    GEMINI_API_KEY: str = ""
    LLM_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    LLM_API_KEY: str = "mock_key"
    LLM_MODEL: str = "gemini-2.0-flash"

    @property
    def effective_llm_api_key(self) -> str:
        """Returns GEMINI_API_KEY if populated, otherwise LLM_API_KEY."""
        if self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip() not in ("mock_key", "your_key_here", ""):
            return self.GEMINI_API_KEY.strip()
        return self.LLM_API_KEY.strip()

    # Vector Embeddings
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_API_KEY: str = "mock_key"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # File Storage
    UPLOAD_DIR: str = "/tmp/uploads" if os.environ.get("VERCEL") else "./uploads"
    MAX_UPLOAD_MB: int = 10
    RATE_LIMIT_PER_MINUTE: int = 120
    SYNC_PROCESSING: bool = bool(os.environ.get("VERCEL"))


@lru_cache
def get_settings() -> Settings:
    return Settings()

