import decimal
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderBase(BaseModel):
    po_number: str = Field(..., max_length=100)
    vendor_name: str = Field(..., max_length=255)
    total_amount: decimal.Decimal = Field(..., decimal_places=2)


class PurchaseOrderCreate(PurchaseOrderBase):
    pass


class PurchaseOrderRead(PurchaseOrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
