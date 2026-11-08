import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.invoice import InvoiceRead
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get(
    "",
    response_model=list[InvoiceRead],
    summary="List extracted invoices for the tenant",
)
async def list_invoices(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
) -> list[InvoiceRead]:
    """Retrieve all invoices extracted for the authenticated tenant."""
    invoices = await InvoiceService.list_invoices(
        session=session,
        tenant_id=current_user.tenant_id,
        limit=limit,
        offset=offset,
    )
    return [InvoiceRead.model_validate(inv) for inv in invoices]


@router.get(
    "/{invoice_id}",
    response_model=InvoiceRead,
    summary="Get invoice by ID",
)
async def get_invoice(
    invoice_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    """Retrieve a single invoice with tenant boundary enforcement."""
    invoice = await InvoiceService.get_invoice(
        session=session,
        tenant_id=current_user.tenant_id,
        invoice_id=invoice_id,
    )
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )
    return InvoiceRead.model_validate(invoice)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an extracted invoice and its findings",
)
async def delete_invoice(
    invoice_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an invoice entry and its findings strictly scoped to tenant."""
    await InvoiceService.delete_invoice(
        session=session,
        tenant_id=current_user.tenant_id,
        invoice_id=invoice_id,
    )

