import hashlib
import math
import structlog
from typing import Optional
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


def _generate_deterministic_vector(text: str, dim: int = 1536) -> list[float]:
    """Generate a deterministic, unit-normalized mock vector when LLM API keys are unset/mock."""
    # Hash seed using sha256
    hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(hash_bytes[:8], "big")

    # Generate pseudo-random components based on seed
    raw_vals = []
    curr = seed
    for _ in range(dim):
        curr = (curr * 6364136223846793005 + 1) & 0xFFFFFFFFFFFFFFFF
        # map to [-1.0, 1.0]
        val = ((curr >> 32) / 0xFFFFFFFF) * 2.0 - 1.0
        raw_vals.append(val)

    # Unit normalize
    norm = math.sqrt(sum(x * x for x in raw_vals)) or 1.0
    return [round(x / norm, 6) for x in raw_vals]


class DocumentEmbedder:
    def __init__(self):
        self.dim = settings.EMBEDDING_DIM
        self.api_key = settings.EMBEDDING_API_KEY
        self.base_url = settings.EMBEDDING_BASE_URL
        self.model = settings.EMBEDDING_MODEL
        self._client: Optional[OpenAIEmbeddings] = None

        # Check if a live API key is configured
        if self.api_key and self.api_key not in ("mock_key", "your_key_here", ""):
            try:
                self._client = OpenAIEmbeddings(
                    model=self.model,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    request_timeout=20.0,
                    max_retries=2,
                )
            except Exception as e:
                logger.warning("Failed to initialize OpenAIEmbeddings, falling back to mock embedder", exc=str(e))
                self._client = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # If live client is available, attempt API call
        if self._client is not None:
            try:
                return self._client.embed_documents(texts)
            except Exception as exc:
                logger.warning("Remote embedding API call failed, falling back to deterministic vector", exc=str(exc))

        # Deterministic vector fallback
        return [_generate_deterministic_vector(t, self.dim) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        if self._client is not None:
            try:
                return self._client.embed_query(text)
            except Exception as exc:
                logger.warning("Remote embedding query failed, using deterministic fallback", exc=str(exc))

        return _generate_deterministic_vector(text, self.dim)


default_embedder = DocumentEmbedder()


def embed_texts(texts: list[str]) -> list[list[float]]:
    return default_embedder.embed_texts(texts)


def embed_query(text: str) -> list[float]:
    return default_embedder.embed_query(text)
