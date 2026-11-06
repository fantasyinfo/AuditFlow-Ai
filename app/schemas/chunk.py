import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    page: int | None = None
    text: str
    created_at: datetime
