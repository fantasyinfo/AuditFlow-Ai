from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.models.finding import FindingSeverity
from app.models.invoice import Invoice
from app.models.purchase_order import PurchaseOrder
from app.schemas.finding import FindingCreate


def check_amount_mismatch(invoice: Invoice, db: Session, **kwargs) -> Optional[FindingCreate]:
    """Check if the invoice total mismatches the associated purchase order amount."""
    if not invoice.po_id:
        return None

    po = db.query(PurchaseOrder).filter(
        PurchaseOrder.id == invoice.po_id,
        PurchaseOrder.tenant_id == invoice.tenant_id,
    ).first()

    if not po:
        return None

    diff = invoice.total_amount - po.total_amount
    if abs(diff) > Decimal("0.01"):
        return FindingCreate(
            rule="amount_mismatch",
            severity=FindingSeverity.HIGH.value,
            reason=(
                f"Amount mismatch detected: Invoice total (₹{invoice.total_amount}) differs "
                f"from linked Purchase Order {po.po_number} total (₹{po.total_amount}) by ₹{diff:+.2f}."
            ),
            evidence={
                "invoice_total": str(invoice.total_amount),
                "po_total": str(po.total_amount),
                "discrepancy": str(diff),
                "po_number": po.po_number,
                "po_id": str(po.id),
            },
        )

    return None
