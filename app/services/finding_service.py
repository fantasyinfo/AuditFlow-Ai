import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding
from app.schemas.finding import FindingUpdate
from app.services.audit_service import AuditService


class FindingService:
    @staticmethod
    async def list_findings(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        status_filter: Optional[str] = None,
        rule_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Finding]:
        """List findings strictly filtered by tenant_id and optional status or rule."""
        query = select(Finding).where(Finding.tenant_id == tenant_id)

        if status_filter:
            query = query.where(Finding.status == status_filter)
        if rule_filter:
            query = query.where(Finding.rule == rule_filter)

        query = query.order_by(Finding.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_finding(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        finding_id: uuid.UUID,
    ) -> Optional[Finding]:
        query = select(Finding).where(
            Finding.id == finding_id,
            Finding.tenant_id == tenant_id,
        )
        result = await session.execute(query)
        return result.scalars().first()

    @staticmethod
    async def update_finding(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        finding_id: uuid.UUID,
        update_data: FindingUpdate,
    ) -> Finding:
        finding = await FindingService.get_finding(session, tenant_id, finding_id)
        if not finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Finding not found.",
            )

        before_state = {
            "status": finding.status,
            "rule": finding.rule,
            "severity": finding.severity,
        }

        finding.status = update_data.status.value
        await session.commit()
        await session.refresh(finding)

        after_state = {
            "status": finding.status,
            "rule": finding.rule,
            "severity": finding.severity,
            "notes": update_data.notes,
        }

        # Create immutable audit log entry
        await AuditService.log_action(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
            action=f"finding.{update_data.status.value}",
            entity="finding",
            entity_id=str(finding.id),
            before=before_state,
            after=after_state,
        )

        return finding
