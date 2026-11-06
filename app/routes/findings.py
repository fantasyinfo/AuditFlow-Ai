import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.audit_log import AuditLogRead
from app.schemas.auth import CurrentUser
from app.schemas.finding import FindingRead, FindingUpdate
from app.services.audit_service import AuditService
from app.services.finding_service import FindingService

router = APIRouter(tags=["Findings & Audit"])


@router.get(
    "/findings",
    response_model=list[FindingRead],
    summary="List audit findings for tenant",
)
async def list_findings(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status: Optional[str] = Query(None, description="Filter by status (open, confirmed, dismissed)"),
    rule: Optional[str] = Query(None, description="Filter by rule name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[FindingRead]:
    """Retrieve audit findings with optional rule and status filters, strictly tenant-scoped."""
    findings = await FindingService.list_findings(
        session=session,
        tenant_id=current_user.tenant_id,
        status_filter=status,
        rule_filter=rule,
        limit=limit,
        offset=offset,
    )
    return [FindingRead.model_validate(f) for f in findings]


@router.get(
    "/findings/{finding_id}",
    response_model=FindingRead,
    summary="Get single finding details",
)
async def get_finding(
    finding_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FindingRead:
    """Retrieve details for a specific finding."""
    finding = await FindingService.get_finding(
        session=session,
        tenant_id=current_user.tenant_id,
        finding_id=finding_id,
    )
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found.",
        )
    return FindingRead.model_validate(finding)


@router.patch(
    "/findings/{finding_id}",
    response_model=FindingRead,
    summary="Confirm or dismiss finding",
)
async def update_finding(
    finding_id: uuid.UUID,
    update_data: FindingUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FindingRead:
    """Confirm or dismiss an audit finding, writing an immutable change entry to the audit log."""
    updated = await FindingService.update_finding(
        session=session,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        finding_id=finding_id,
        update_data=update_data,
    )
    return FindingRead.model_validate(updated)


@router.get(
    "/audit-logs",
    response_model=list[AuditLogRead],
    summary="List audit log entries for tenant",
)
async def list_audit_logs(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[AuditLogRead]:
    """Retrieve immutable audit trail entries for the caller's tenant."""
    logs = await AuditService.list_logs(
        session=session,
        tenant_id=current_user.tenant_id,
        limit=limit,
        offset=offset,
    )
    return [AuditLogRead.model_validate(log) for log in logs]
