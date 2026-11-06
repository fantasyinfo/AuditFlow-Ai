from typing import Optional
from sqlalchemy.orm import Session

from app.models.finding import FindingSeverity
from app.models.invoice import Invoice
from app.schemas.finding import FindingCreate


def check_missing_evidence(invoice: Invoice, db: Session, **kwargs) -> Optional[FindingCreate]:
    """Flag invoices that lack an approved purchase order reference or source documentation."""
    if invoice.po_id is None:
        return FindingCreate(
            rule="missing_evidence",
            severity=FindingSeverity.MEDIUM.value,
            reason=(
                f"Missing supporting evidence: Invoice '{invoice.invoice_number}' from '{invoice.vendor_name}' "
                f"for ₹{invoice.total_amount} was submitted without a linked purchase order reference."
            ),
            evidence={
                "has_po": False,
                "document_id": str(invoice.document_id) if invoice.document_id else None,
                "vendor_name": invoice.vendor_name,
                "amount": str(invoice.total_amount),
            },
        )

    return None
