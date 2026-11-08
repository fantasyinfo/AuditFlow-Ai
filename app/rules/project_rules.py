import decimal
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.project import Project
from app.schemas.finding import FindingCreate, FindingSeverity


def check_project_budget_and_caps(invoice: Invoice, db: Session) -> list[FindingCreate]:
    """Evaluates project-level quotation caps, cumulative budget over-billing, and single invoice limits."""
    findings: list[FindingCreate] = []

    if not invoice.project_id:
        # Check if any project exists matching this vendor
        matching_project = (
            db.query(Project)
            .filter(
                Project.tenant_id == invoice.tenant_id,
                Project.vendor_name.ilike(invoice.vendor_name),
            )
            .first()
        )
        if matching_project:
            invoice.project_id = matching_project.id
            db.flush()

    if not invoice.project_id:
        return findings

    project = db.query(Project).filter(Project.id == invoice.project_id).first()
    if not project:
        return findings

    # 1. Update net and tax amounts if not already set
    if invoice.tax_amount == 0 and invoice.net_amount == 0 and invoice.total_amount > 0:
        if project.gst_rate_percent > 0:
            factor = decimal.Decimal("1.00") + (project.gst_rate_percent / decimal.Decimal("100.00"))
            net = (invoice.total_amount / factor).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)
            invoice.net_amount = net
            invoice.tax_amount = invoice.total_amount - net
        else:
            invoice.net_amount = invoice.total_amount
            invoice.tax_amount = decimal.Decimal("0.00")
        db.flush()

    # 2. Single Invoice Cap Check
    if project.single_invoice_cap and invoice.total_amount > project.single_invoice_cap:
        findings.append(
            FindingCreate(
                rule="project_cap_exceeded",
                severity=FindingSeverity.HIGH.value,
                reason=(
                    f"Invoice {invoice.invoice_number} for ₹{invoice.total_amount:.2f} exceeds "
                    f"the maximum single invoice cap of ₹{project.single_invoice_cap:.2f} "
                    f"stipulated for project '{project.name}'."
                ),
                evidence={
                    "project_id": str(project.id),
                    "project_name": project.name,
                    "invoice_number": invoice.invoice_number,
                    "invoice_amount": str(invoice.total_amount),
                    "single_invoice_cap": str(project.single_invoice_cap),
                },
            )
        )

    # 3. Cumulative Project Budget & Over-logging Check
    if project.budget_amount > decimal.Decimal("0.00"):
        total_invoiced_res = (
            db.query(func.coalesce(func.sum(Invoice.total_amount), decimal.Decimal("0.00")))
            .filter(
                Invoice.tenant_id == invoice.tenant_id,
                Invoice.project_id == project.id,
            )
            .scalar()
        ) or decimal.Decimal("0.00")

        # Tolerance ceiling
        tolerance_multiplier = decimal.Decimal("1.00") + (project.over_billing_tolerance_percent / decimal.Decimal("100.00"))
        allowed_ceiling = project.budget_amount * tolerance_multiplier

        if total_invoiced_res > allowed_ceiling:
            over_amount = total_invoiced_res - project.budget_amount
            over_percent = ((over_amount / project.budget_amount) * decimal.Decimal("100.00")).quantize(
                decimal.Decimal("0.1"), rounding=decimal.ROUND_HALF_UP
            )
            findings.append(
                FindingCreate(
                    rule="project_overbudget",
                    severity=FindingSeverity.CRITICAL.value if over_percent > 15 else FindingSeverity.HIGH.value,
                    reason=(
                        f"Cumulative billing for project '{project.name}' has reached ₹{total_invoiced_res:.2f}, "
                        f"over-logging the agreed quotation baseline (₹{project.budget_amount:.2f}) by "
                        f"+{over_percent}% (over-logged by ₹{over_amount:.2f}, permitted tolerance: {project.over_billing_tolerance_percent}%)."
                    ),
                    evidence={
                        "project_id": str(project.id),
                        "project_name": project.name,
                        "budget_amount": str(project.budget_amount),
                        "total_invoiced": str(total_invoiced_res),
                        "over_amount": str(over_amount),
                        "over_percent": str(over_percent),
                        "tolerance_percent": str(project.over_billing_tolerance_percent),
                    },
                )
            )

    return findings

