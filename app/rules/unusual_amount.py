from decimal import Decimal
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.finding import FindingSeverity
from app.models.invoice import Invoice
from app.schemas.finding import FindingCreate


def check_unusual_amount(invoice: Invoice, db: Session, **kwargs) -> Optional[FindingCreate]:
    """Detect invoices where the total is significantly higher than historical vendor average."""
    # Query historical invoices for this vendor within the tenant
    stats = db.query(
        func.avg(Invoice.total_amount).label("avg_amount"),
        func.count(Invoice.id).label("invoice_count"),
    ).filter(
        Invoice.tenant_id == invoice.tenant_id,
        Invoice.vendor_name == invoice.vendor_name,
        Invoice.id != invoice.id,
    ).first()

    if not stats or not stats.invoice_count or stats.invoice_count < 2:
        # Insufficient history to determine anomaly baseline
        return None

    avg_amt = Decimal(str(stats.avg_amount))
    multiplier_threshold = Decimal("2.5")

    if invoice.total_amount > (avg_amt * multiplier_threshold):
        ratio = invoice.total_amount / avg_amt
        return FindingCreate(
            rule="unusual_amount",
            severity=FindingSeverity.HIGH.value,
            reason=(
                f"Unusual spike detected: Invoice amount (₹{invoice.total_amount}) is {ratio:.1f}x higher "
                f"than the historical average (₹{avg_amt:.2f}) for vendor '{invoice.vendor_name}'."
            ),
            evidence={
                "invoice_amount": str(invoice.total_amount),
                "historical_average": str(round(avg_amt, 2)),
                "multiplier": f"{ratio:.2f}",
                "historical_count": stats.invoice_count,
                "vendor_name": invoice.vendor_name,
            },
        )

    return None
