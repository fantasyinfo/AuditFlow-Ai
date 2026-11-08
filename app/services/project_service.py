import decimal
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.finding import Finding, FindingStatus
from app.models.invoice import Invoice
from app.models.project import Project, ProjectStatus
from app.schemas.project import (
    DocumentReconciliationItem,
    InvoiceReconciliationItem,
    PaymentRecordRequest,
    ProjectCreate,
    ProjectReconciliationResponse,
    ProjectResponse,
    ProjectSummaryItem,
    ProjectUpdate,
)


class ProjectService:
    @staticmethod
    def _compute_net_tax(total: decimal.Decimal, gst_rate: decimal.Decimal) -> tuple[decimal.Decimal, decimal.Decimal]:
        """Calculates net amount without GST and tax portion from total amount."""
        if gst_rate <= decimal.Decimal("0.00") or total <= decimal.Decimal("0.00"):
            return total, decimal.Decimal("0.00")
        factor = decimal.Decimal("1.00") + (gst_rate / decimal.Decimal("100.00"))
        net = (total / factor).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
        tax = total - net
        return net, tax

    @classmethod
    async def list_projects(
        cls,
        session: AsyncSession,
        tenant_id: uuid.UUID,
    ) -> list[ProjectSummaryItem]:
        """List all projects for a tenant with calculated financial summaries."""
        stmt = select(Project).where(Project.tenant_id == tenant_id).order_by(Project.created_at.desc())
        result = await session.execute(stmt)
        projects = list(result.scalars().all())

        summaries = []
        for p in projects:
            # Query invoices for this project
            inv_stmt = select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                Invoice.project_id == p.id,
            )
            inv_res = await session.execute(inv_stmt)
            invoices = list(inv_res.scalars().all())

            # Query documents count
            doc_count_stmt = select(func.count(Document.id)).where(
                Document.tenant_id == tenant_id,
                Document.project_id == p.id,
            )
            doc_count_res = await session.execute(doc_count_stmt)
            doc_count = doc_count_res.scalar() or 0

            # Query open findings count
            findings_count_stmt = select(func.count(Finding.id)).where(
                Finding.tenant_id == tenant_id,
                Finding.project_id == p.id,
                Finding.status == FindingStatus.OPEN.value,
            )
            findings_count_res = await session.execute(findings_count_stmt)
            open_findings_count = findings_count_res.scalar() or 0

            # Sum financial metrics
            total_invoiced_gross = sum((inv.total_amount for inv in invoices), decimal.Decimal("0.00"))
            total_paid_gross = sum((inv.paid_amount for inv in invoices), decimal.Decimal("0.00"))
            total_invoiced_net = decimal.Decimal("0.00")
            total_invoiced_gst = decimal.Decimal("0.00")

            for inv in invoices:
                if inv.tax_amount > 0 or inv.net_amount > 0:
                    total_invoiced_net += inv.net_amount
                    total_invoiced_gst += inv.tax_amount
                else:
                    net, tax = cls._compute_net_tax(inv.total_amount, p.gst_rate_percent)
                    total_invoiced_net += net
                    total_invoiced_gst += tax

            budget = p.budget_amount
            variance_amount = total_invoiced_gross - budget
            if budget > decimal.Decimal("0.00"):
                variance_percent = ((variance_amount / budget) * decimal.Decimal("100.00")).quantize(
                    decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
                )
                burn_rate_percent = ((total_invoiced_gross / budget) * decimal.Decimal("100.00")).quantize(
                    decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
                )
            else:
                variance_percent = decimal.Decimal("0.00")
                burn_rate_percent = decimal.Decimal("0.00")

            remaining_balance = budget - total_paid_gross

            summaries.append(
                ProjectSummaryItem(
                    id=p.id,
                    tenant_id=p.tenant_id,
                    name=p.name,
                    code=p.code,
                    description=p.description,
                    vendor_name=p.vendor_name,
                    vendor_gstin=p.vendor_gstin,
                    status=p.status,
                    budget_amount=p.budget_amount,
                    budget_currency=p.budget_currency,
                    gst_rate_percent=p.gst_rate_percent,
                    over_billing_tolerance_percent=p.over_billing_tolerance_percent,
                    single_invoice_cap=p.single_invoice_cap,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    total_invoiced_gross=total_invoiced_gross,
                    total_invoiced_net=total_invoiced_net,
                    total_invoiced_gst=total_invoiced_gst,
                    total_paid_gross=total_paid_gross,
                    remaining_balance=remaining_balance,
                    variance_amount=variance_amount,
                    variance_percent=variance_percent,
                    burn_rate_percent=burn_rate_percent,
                    is_over_logged=total_invoiced_gross > budget,
                    documents_count=doc_count,
                    invoices_count=len(invoices),
                    open_findings_count=open_findings_count,
                )
            )

        return summaries

    @classmethod
    async def create_project(
        cls,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        data: ProjectCreate,
    ) -> Project:
        """Create a new audit project scoped to tenant."""
        # Check code uniqueness
        existing_stmt = select(Project).where(
            Project.tenant_id == tenant_id,
            Project.code == data.code,
        )
        existing = (await session.execute(existing_stmt)).scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project with code '{data.code}' already exists in your workspace.",
            )

        project = Project(
            tenant_id=tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            vendor_name=data.vendor_name,
            vendor_gstin=data.vendor_gstin,
            status=ProjectStatus.ACTIVE.value,
            budget_amount=data.budget_amount,
            budget_currency=data.budget_currency,
            gst_rate_percent=data.gst_rate_percent,
            over_billing_tolerance_percent=data.over_billing_tolerance_percent,
            single_invoice_cap=data.single_invoice_cap,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        # Automatically link any existing orphan documents/invoices from this vendor to this new project
        await cls._auto_link_vendor_entities(session, tenant_id, project)
        return project

    @staticmethod
    async def _auto_link_vendor_entities(session: AsyncSession, tenant_id: uuid.UUID, project: Project) -> None:
        """Helper to associate existing unassigned invoices/documents from the same vendor to this project."""
        invoices_stmt = select(Invoice).where(
            Invoice.tenant_id == tenant_id,
            Invoice.vendor_name.ilike(project.vendor_name),
            Invoice.project_id.is_(None),
        )
        res = await session.execute(invoices_stmt)
        matched_invoices = list(res.scalars().all())

        for inv in matched_invoices:
            inv.project_id = project.id
            if inv.tax_amount == 0 and inv.net_amount == 0 and inv.total_amount > 0:
                net, tax = ProjectService._compute_net_tax(inv.total_amount, project.gst_rate_percent)
                inv.net_amount = net
                inv.tax_amount = tax

            # Link findings for this invoice
            finding_stmt = select(Finding).where(
                Finding.tenant_id == tenant_id,
                Finding.invoice_id == inv.id,
                Finding.project_id.is_(None),
            )
            finding_res = await session.execute(finding_stmt)
            for f in finding_res.scalars().all():
                f.project_id = project.id

            # Link document
            if inv.document_id:
                doc_stmt = select(Document).where(
                    Document.tenant_id == tenant_id,
                    Document.id == inv.document_id,
                    Document.project_id.is_(None),
                )
                doc_res = await session.execute(doc_stmt)
                doc = doc_res.scalars().first()
                if doc:
                    doc.project_id = project.id

        if matched_invoices:
            await session.commit()

    @staticmethod
    async def get_project(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Project:
        """Retrieve project within tenant boundary."""
        stmt = select(Project).where(
            Project.id == project_id,
            Project.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        project = result.scalars().first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit project not found.",
            )
        return project

    @classmethod
    async def update_project(
        cls,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        data: ProjectUpdate,
    ) -> Project:
        """Update project configuration and quotation limits."""
        project = await cls.get_project(session, tenant_id, project_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(project, key, value)

        await session.commit()
        await session.refresh(project)
        return project

    @classmethod
    async def delete_project(
        cls,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> bool:
        """Delete an audit project (idempotent: safe if already deleted)."""
        stmt = select(Project).where(
            Project.id == project_id,
            Project.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        project = result.scalars().first()
        if not project:
            return True
        await session.delete(project)
        await session.commit()
        return True

    @classmethod
    async def get_project_reconciliation(
        cls,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ProjectReconciliationResponse:
        """Detailed quotation baseline vs actual invoicing, over/under logged % and GST dissection."""
        project = await cls.get_project(session, tenant_id, project_id)

        # 1. Quotation baseline computation
        quoted_gross = project.budget_amount
        quoted_net, quoted_gst = cls._compute_net_tax(quoted_gross, project.gst_rate_percent)

        # 2. Invoices retrieval & dissection
        inv_stmt = select(Invoice).where(
            Invoice.tenant_id == tenant_id,
            Invoice.project_id == project.id,
        ).order_by(Invoice.invoice_date.desc().nullslast(), Invoice.created_at.desc())
        inv_res = await session.execute(inv_stmt)
        invoices = list(inv_res.scalars().all())

        invoice_items: list[InvoiceReconciliationItem] = []
        total_invoiced_gross = decimal.Decimal("0.00")
        total_invoiced_net = decimal.Decimal("0.00")
        total_invoiced_gst = decimal.Decimal("0.00")
        total_paid_gross = decimal.Decimal("0.00")

        needs_commit = False
        for inv in invoices:
            # Backfill net/tax if not calculated
            if (inv.tax_amount == 0 and inv.net_amount == 0 and inv.total_amount > 0):
                net, tax = cls._compute_net_tax(inv.total_amount, project.gst_rate_percent)
                inv.net_amount = net
                inv.tax_amount = tax
                needs_commit = True

            total_invoiced_gross += inv.total_amount
            total_invoiced_net += inv.net_amount
            total_invoiced_gst += inv.tax_amount
            total_paid_gross += inv.paid_amount

            remaining_unpaid = max(decimal.Decimal("0.00"), inv.total_amount - inv.paid_amount)
            invoice_items.append(
                InvoiceReconciliationItem(
                    id=inv.id,
                    invoice_number=inv.invoice_number,
                    invoice_date=inv.invoice_date,
                    total_amount=inv.total_amount,
                    tax_amount=inv.tax_amount,
                    net_amount=inv.net_amount,
                    paid_amount=inv.paid_amount,
                    remaining_unpaid=remaining_unpaid,
                    payment_status=inv.payment_status,
                    po_id=inv.po_id,
                    created_at=inv.created_at,
                )
            )

        if needs_commit:
            await session.commit()

        # 3. Documents
        doc_stmt = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.project_id == project.id,
        ).order_by(Document.created_at.desc())
        doc_res = await session.execute(doc_stmt)
        documents = [
            DocumentReconciliationItem(
                id=d.id,
                filename=d.filename,
                type=d.type,
                status=d.status,
                created_at=d.created_at,
            )
            for d in doc_res.scalars().all()
        ]

        # 4. Findings
        findings_count_stmt = select(func.count(Finding.id)).where(
            Finding.tenant_id == tenant_id,
            Finding.project_id == project.id,
        )
        open_findings_stmt = select(func.count(Finding.id)).where(
            Finding.tenant_id == tenant_id,
            Finding.project_id == project.id,
            Finding.status == FindingStatus.OPEN.value,
        )
        findings_count = (await session.execute(findings_count_stmt)).scalar() or 0
        open_findings_count = (await session.execute(open_findings_stmt)).scalar() or 0

        # 5. Over/under-logged & burn calculations
        variance_amount = total_invoiced_gross - quoted_gross
        if quoted_gross > decimal.Decimal("0.00"):
            variance_percent = ((variance_amount / quoted_gross) * decimal.Decimal("100.00")).quantize(
                decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
            )
            burn_rate_percent = ((total_invoiced_gross / quoted_gross) * decimal.Decimal("100.00")).quantize(
                decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
            )
        else:
            variance_percent = decimal.Decimal("0.00")
            burn_rate_percent = decimal.Decimal("0.00")

        is_over_logged = total_invoiced_gross > quoted_gross
        over_logged_amount = max(decimal.Decimal("0.00"), variance_amount)
        under_logged_amount = max(decimal.Decimal("0.00"), -variance_amount)
        tolerance_breached = variance_percent > project.over_billing_tolerance_percent

        total_unpaid_gross = max(decimal.Decimal("0.00"), total_invoiced_gross - total_paid_gross)
        remaining_balance_under_quotation = quoted_gross - total_paid_gross
        uncommitted_budget = max(decimal.Decimal("0.00"), quoted_gross - total_invoiced_gross)

        return ProjectReconciliationResponse(
            project=ProjectResponse.model_validate(project),
            quoted_gross=quoted_gross,
            quoted_net=quoted_net,
            quoted_gst=quoted_gst,
            gst_rate_percent=project.gst_rate_percent,
            total_invoiced_gross=total_invoiced_gross,
            total_invoiced_net=total_invoiced_net,
            total_invoiced_gst=total_invoiced_gst,
            invoice_count=len(invoices),
            total_paid_gross=total_paid_gross,
            total_unpaid_gross=total_unpaid_gross,
            remaining_balance_under_quotation=remaining_balance_under_quotation,
            uncommitted_budget=uncommitted_budget,
            variance_amount=variance_amount,
            variance_percent=variance_percent,
            burn_rate_percent=burn_rate_percent,
            is_over_logged=is_over_logged,
            over_logged_amount=over_logged_amount,
            under_logged_amount=under_logged_amount,
            tolerance_breached=tolerance_breached,
            invoices=invoice_items,
            documents=documents,
            findings_count=findings_count,
            open_findings_count=open_findings_count,
        )

    @classmethod
    async def record_payment(
        cls,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        invoice_id: uuid.UUID,
        payment_req: PaymentRecordRequest,
    ) -> InvoiceReconciliationItem:
        """Record a partial or full payment against an invoice under this project."""
        await cls.get_project(session, tenant_id, project_id)

        inv_stmt = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant_id,
            Invoice.project_id == project_id,
        )
        res = await session.execute(inv_stmt)
        invoice = res.scalars().first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found under this project.",
            )

        new_paid = invoice.paid_amount + payment_req.paid_amount
        invoice.paid_amount = new_paid
        if new_paid >= invoice.total_amount:
            invoice.payment_status = "paid"
        else:
            invoice.payment_status = "partially_paid"

        await session.commit()
        await session.refresh(invoice)

        remaining_unpaid = max(decimal.Decimal("0.00"), invoice.total_amount - invoice.paid_amount)
        return InvoiceReconciliationItem(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            total_amount=invoice.total_amount,
            tax_amount=invoice.tax_amount,
            net_amount=invoice.net_amount,
            paid_amount=invoice.paid_amount,
            remaining_unpaid=remaining_unpaid,
            payment_status=invoice.payment_status,
            po_id=invoice.po_id,
            created_at=invoice.created_at,
        )

