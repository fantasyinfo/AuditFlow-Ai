import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.finding import FindingSeverity, FindingStatus


class FindingBase(BaseModel):
    rule: str
    severity: str = FindingSeverity.MEDIUM.value
    reason: str
    evidence: dict | None = None


class FindingCreate(FindingBase):
    pass


class FindingUpdate(BaseModel):
    status: FindingStatus = Field(..., description="Target status: confirmed or dismissed")
    notes: str | None = None


class FindingRead(FindingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    invoice_id: uuid.UUID
    status: str
    created_at: datetime
