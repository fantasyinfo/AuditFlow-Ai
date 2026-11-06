from typing import Optional
import structlog
from langchain_openai import ChatOpenAI

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


def is_live_llm_configured() -> bool:
    """Check if a genuine, non-mock LLM API key has been provided in the environment."""
    key = settings.LLM_API_KEY.strip()
    return bool(key and key not in ("mock_key", "your_key_here", "dummy_key", "none"))


def get_chat_model(
    temperature: float = 0.0,
    max_tokens: int = 1000,
    timeout: float = 25.0,
) -> Optional[ChatOpenAI]:
    """Build the ChatOpenAI client with configured base URL and credentials."""
    if not is_live_llm_configured():
        return None

    try:
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=2,
        )
    except Exception as exc:
        logger.warning("Failed to initialize ChatOpenAI client", exc=str(exc))
        return None
