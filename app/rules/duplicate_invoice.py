from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.finding import FindingSeverity
from app.models.invoice import Invoice
from app.schemas.finding import FindingCreate


def check_duplicate_invoice(invoice: Invoice, db: Session, **kwargs) -> Optional[FindingCreate]:
    """Check for duplicate invoices by (vendor, invoice_number) or (vendor, amount, date)."""
    # 1. Check exact match: same vendor and same invoice number
    query_exact = db.query(Invoice).filter(
        Invoice.tenant_id == invoice.tenant_id,
        Invoice.vendor_name == invoice.vendor_name,
        Invoice.invoice_number == invoice.invoice_number,
        Invoice.id != invoice.id,
    )
    duplicate_by_num = query_exact.first()
    if duplicate_by_num:
        return FindingCreate(
            rule="duplicate_invoice",
            severity=FindingSeverity.CRITICAL.value,
            reason=(
                f"Duplicate invoice detected: Invoice '{invoice.invoice_number}' from vendor "
                f"'{invoice.vendor_name}' matches existing invoice ID {duplicate_by_num.id}."
            ),
            evidence={
                "duplicate_type": "vendor_and_number",
                "conflicting_invoice_id": str(duplicate_by_num.id),
                "conflicting_invoice_number": duplicate_by_num.invoice_number,
                "vendor_name": invoice.vendor_name,
                "amount": str(invoice.total_amount),
            },
        )

    # 2. Check match by vendor + total_amount + invoice_date (if date is present)
    if invoice.invoice_date is not None:
        query_amount_date = db.query(Invoice).filter(
            Invoice.tenant_id == invoice.tenant_id,
            Invoice.vendor_name == invoice.vendor_name,
            Invoice.total_amount == invoice.total_amount,
            Invoice.invoice_date == invoice.invoice_date,
            Invoice.id != invoice.id,
        )
        duplicate_by_amt_date = query_amount_date.first()
        if duplicate_by_amt_date:
            return FindingCreate(
                rule="duplicate_invoice",
                severity=FindingSeverity.CRITICAL.value,
                reason=(
                    f"Possible duplicate invoice detected: Vendor '{invoice.vendor_name}' submitted "
                    f"an invoice with identical total (₹{invoice.total_amount}) and date "
                    f"({invoice.invoice_date}) matching invoice '{duplicate_by_amt_date.invoice_number}'."
                ),
                evidence={
                    "duplicate_type": "vendor_amount_date",
                    "conflicting_invoice_id": str(duplicate_by_amt_date.id),
                    "conflicting_invoice_number": duplicate_by_amt_date.invoice_number,
                    "vendor_name": invoice.vendor_name,
                    "amount": str(invoice.total_amount),
                    "date": str(invoice.invoice_date),
                },
            )

    return None
