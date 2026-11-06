import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentStatus, DocumentType


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    message: str = "Document uploaded successfully and queued for processing."


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    filename: str
    type: str
    status: str
    storage_path: str
    created_by: uuid.UUID | None = None
    error_message: str | None = None
    created_at: datetime
