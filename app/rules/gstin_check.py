import re
from typing import Optional
from sqlalchemy.orm import Session

from app.models.finding import FindingSeverity
from app.models.invoice import Invoice
from app.schemas.finding import FindingCreate

# Standard 15-character Indian Goods and Services Tax Identification Number (GSTIN)
GSTIN_STRICT_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


def check_invalid_gstin(invoice: Invoice, db: Session, **kwargs) -> Optional[FindingCreate]:
    """Validate format of Indian GSTIN for tax compliance."""
    if not invoice.vendor_gstin:
        return FindingCreate(
            rule="invalid_gstin",
            severity=FindingSeverity.MEDIUM.value,
            reason=(
                f"Missing GSTIN: Vendor '{invoice.vendor_name}' does not have a registered GSTIN "
                f"on invoice '{invoice.invoice_number}'."
            ),
            evidence={
                "gstin_provided": None,
                "vendor_name": invoice.vendor_name,
                "invoice_number": invoice.invoice_number,
            },
        )

    clean_gstin = invoice.vendor_gstin.strip().upper()
    if not GSTIN_STRICT_REGEX.match(clean_gstin):
        return FindingCreate(
            rule="invalid_gstin",
            severity=FindingSeverity.MEDIUM.value,
            reason=(
                f"Invalid GSTIN format: '{invoice.vendor_gstin}' from vendor '{invoice.vendor_name}' "
                f"violates standard 15-character Indian GSTIN structure."
            ),
            evidence={
                "gstin_provided": invoice.vendor_gstin,
                "vendor_name": invoice.vendor_name,
                "expected_format": "2 digits + 10-char PAN + 1 entity num + 'Z' + 1 check char",
            },
        )

    return None
