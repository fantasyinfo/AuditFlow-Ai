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
        document_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Invoice]:
        """List all invoices belonging strictly to the caller's tenant, optionally filtered by document."""
        conditions = [Invoice.tenant_id == tenant_id]
        if document_id:
            conditions.append(Invoice.document_id == document_id)

        query = (
            select(Invoice)
            .where(*conditions)
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

    @staticmethod
    async def delete_invoice(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
    ) -> bool:
        """Delete an invoice and its cascaded findings strictly within tenant."""
        query = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant_id,
        )
        result = await session.execute(query)
        invoice = result.scalars().first()
        if not invoice:
            return True

        await session.delete(invoice)
        await session.commit()
        return True

