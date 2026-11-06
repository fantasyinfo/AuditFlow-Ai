import uuid
from typing import Optional
from pydantic import BaseModel, Field


class AgentAskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="The audit or document question to ask")


class AgentCitation(BaseModel):
    source: str = Field(..., description="Citation marker, e.g. [invoice_1042.pdf p.1] or [finding #ID]")
    kind: str = Field(..., description="'document' or 'finding'")
    document_id: Optional[uuid.UUID] = None
    page: Optional[int] = None
    finding_id: Optional[uuid.UUID] = None


class AgentAskResponse(BaseModel):
    query: str
    answer: str
    citations: list[str] = Field(default_factory=list, description="List of source citations used in the answer")
    answered_from_sources: bool = Field(..., description="Whether the answer was derived from verified tenant documents/findings")
