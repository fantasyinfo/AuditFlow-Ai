import time
import structlog
import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Per-tenant / client IP rate limiter in Redis enforcing RATE_LIMIT_PER_MINUTE."""

    def __init__(self, app):
        super().__init__(app)
        self.redis_client = None
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.0,
            )
        except Exception as e:
            logger.warning("Redis not available for rate limiting; fail-open mode", error=str(e))

    async def dispatch(self, request: Request, call_next):
        # Exclude static assets, docs, metrics, and health endpoints
        path = request.url.path
        if (
            path.startswith("/assets")
            or path.startswith("/metrics")
            or path.startswith("/health")
            or path.startswith("/docs")
            or path.startswith("/openapi.json")
            or path in ("/", "/app", "/admin", "/ui")
        ):
            return await call_next(request)

        if not self.redis_client:
            return await call_next(request)

        # Identify client by Authorization token / tenant or Client IP
        auth_header = request.headers.get("Authorization", "")
        client_key = auth_header[-16:] if len(auth_header) > 16 else (request.client.host if request.client else "unknown")
        current_minute = int(time.time() // 60)
        redis_key = f"ratelimit:{client_key}:{current_minute}"

        try:
            current_count = await self.redis_client.incr(redis_key)
            if current_count == 1:
                await self.redis_client.expire(redis_key, 65)

            limit = settings.RATE_LIMIT_PER_MINUTE
            if current_count > limit:
                logger.warning("Rate limit exceeded", client=client_key, count=current_count, limit=limit)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. Maximum {limit} requests per minute.",
                        "retry_after_seconds": 60 - int(time.time() % 60),
                    },
                    headers={"Retry-After": str(60 - int(time.time() % 60))},
                )
        except Exception as exc:
            # Fail open if Redis is temporarily unreachable
            logger.debug("Rate limiting check failed; permitting request", error=str(exc))

        return await call_next(request)
