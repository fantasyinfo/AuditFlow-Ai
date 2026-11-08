import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.document import Document
from app.models.invoice import Invoice
from app.schemas.auth import CurrentUser
from app.schemas.project import (
    InvoiceReconciliationItem,
    PaymentRecordRequest,
    ProjectCreate,
    ProjectListResponse,
    ProjectReconciliationResponse,
    ProjectResponse,
    ProjectSummaryItem,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Audit Projects & Budget Workspaces"])


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List all audit projects with quotation baselines and burn-rate summaries",
)
async def list_projects(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectListResponse:
    """Retrieve all audit projects with calculated financial summaries, over-logged percentages and findings."""
    items = await ProjectService.list_projects(session, current_user.tenant_id)
    return ProjectListResponse(projects=items, total=len(items))


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new audit project workspace with quotation baseline",
)
async def create_project(
    data: ProjectCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Instantiate a new project engagement with vendor agreement details, quotation cap, and GST rates."""
    project = await ProjectService.create_project(session, current_user.tenant_id, data)
    return ProjectResponse.model_validate(project)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get audit project details",
)
async def get_project(
    project_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Retrieve single project by ID strictly scoped to tenant."""
    project = await ProjectService.get_project(session, current_user.tenant_id, project_id)
    return ProjectResponse.model_validate(project)


@router.get(
    "/{project_id}/reconciliation",
    response_model=ProjectReconciliationResponse,
    summary="Get complete financial reconciliation: Quotation vs Invoices, Over-logged %, GST breakdown, and Paid vs Left",
)
async def get_project_reconciliation(
    project_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectReconciliationResponse:
    """Calculate and return full budget burn rate, net amount without GST, remaining balance, and invoice status."""
    return await ProjectService.get_project_reconciliation(session, current_user.tenant_id, project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update audit project settings, quotation budget or caps",
)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    """Update project configuration, budget limits, or tolerances."""
    project = await ProjectService.update_project(session, current_user.tenant_id, project_id, data)
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an audit project",
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete audit project workspace."""
    await ProjectService.delete_project(session, current_user.tenant_id, project_id)


@router.post(
    "/{project_id}/invoices/{invoice_id}/payments",
    response_model=InvoiceReconciliationItem,
    summary="Record payment against an invoice to track paid vs remaining balance",
)
async def record_payment(
    project_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payment_req: PaymentRecordRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceReconciliationItem:
    """Record payment made against a project invoice and update outstanding balances."""
    return await ProjectService.record_payment(
        session, current_user.tenant_id, project_id, invoice_id, payment_req
    )


@router.post(
    "/{project_id}/link-invoice/{invoice_id}",
    summary="Manually link an invoice to this audit project",
)
async def link_invoice(
    project_id: uuid.UUID,
    invoice_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Manually assign an invoice to an audit project."""
    project = await ProjectService.get_project(session, current_user.tenant_id, project_id)
    inv_stmt = select(Invoice).where(
        Invoice.id == invoice_id,
        Invoice.tenant_id == current_user.tenant_id,
    )
    inv = (await session.execute(inv_stmt)).scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    inv.project_id = project.id
    if inv.tax_amount == 0 and inv.net_amount == 0 and inv.total_amount > 0:
        net, tax = ProjectService._compute_net_tax(inv.total_amount, project.gst_rate_percent)
        inv.net_amount = net
        inv.tax_amount = tax

    await session.commit()
    return {"status": "linked", "project_id": str(project.id), "invoice_id": str(inv.id)}


@router.post(
    "/{project_id}/link-document/{document_id}",
    summary="Manually link a document to this audit project",
)
async def link_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Manually assign a document to an audit project."""
    project = await ProjectService.get_project(session, current_user.tenant_id, project_id)
    doc_stmt = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == current_user.tenant_id,
    )
    doc = (await session.execute(doc_stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc.project_id = project.id
    await session.commit()
    return {"status": "linked", "project_id": str(project.id), "document_id": str(doc.id)}

