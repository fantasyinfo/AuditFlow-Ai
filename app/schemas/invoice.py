import decimal
import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class InvoiceBase(BaseModel):
    vendor_name: str = Field(..., max_length=255)
    vendor_gstin: str | None = Field(default=None, max_length=50)
    invoice_number: str = Field(..., max_length=100)
    invoice_date: date | None = None
    total_amount: decimal.Decimal = Field(..., decimal_places=2)
    po_id: uuid.UUID | None = None


class InvoiceCreate(InvoiceBase):
    document_id: uuid.UUID | None = None


class InvoiceRead(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    document_id: uuid.UUID | None = None
    created_at: datetime
