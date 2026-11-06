import hashlib
import json
import uuid
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency import IdempotencyKey


class IdempotencyService:
    @staticmethod
    async def get_response(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        key: str,
    ) -> Optional[dict[str, Any]]:
        """Check if an idempotency key was previously processed for this tenant."""
        query = select(IdempotencyKey).where(
            IdempotencyKey.tenant_id == tenant_id,
            IdempotencyKey.key == key,
        )
        result = await session.execute(query)
        record = result.scalars().first()
        if record:
            return {
                "status_code": record.response_code,
                "body": json.loads(record.response_body),
            }
        return None

    @staticmethod
    async def record_response(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        key: str,
        status_code: int,
        body: dict[str, Any],
    ) -> None:
        """Store the processed response under the tenant's idempotency key."""
        body_str = json.dumps(body)
        body_hash = hashlib.sha256(body_str.encode("utf-8")).hexdigest()

        record = IdempotencyKey(
            tenant_id=tenant_id,
            key=key,
            response_hash=body_hash,
            response_code=status_code,
            response_body=body_str,
        )
        session.add(record)
        await session.commit()
