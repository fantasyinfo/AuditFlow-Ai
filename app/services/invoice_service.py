import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice


class InvoiceService:
    @staticmethod
    async def list_invoices(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Invoice]:
        """List all invoices belonging strictly to the caller's tenant."""
        query = (
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id)
            .order_by(Invoice.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_invoice(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
    ) -> Optional[Invoice]:
        """Retrieve a specific invoice strictly filtered by tenant_id."""
        query = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant_id,
        )
        result = await session.execute(query)
        return result.scalars().first()
