import uuid
from dataclasses import dataclass
from typing import Optional
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.rag.embedder import embed_query

logger = structlog.get_logger()


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int
    chunk_index: int
    text: str
    similarity_score: float

    @property
    def citation(self) -> str:
        return f"[{self.filename} p.{self.page}]"


async def search_chunks(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    query: str,
    limit: int = 5,
) -> list[RetrievedChunk]:
    """Retrieve top-K document chunks for a specific tenant using pgvector cosine similarity."""
    if not query.strip():
        return []

    # 1. Embed query
    query_vector = embed_query(query)

    # 2. Compute cosine distance: document_chunks.embedding <=> query_vector
    dist = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")

    stmt = (
        select(DocumentChunk, Document.filename, dist)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.tenant_id == tenant_id,
            Document.tenant_id == tenant_id,  # Strict multi-tenancy double-guard
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(dist)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    retrieved = []
    for chunk, filename, distance in rows:
        # Cosine distance ranges [0, 2]; similarity is 1.0 - distance
        score = max(0.0, min(1.0, 1.0 - float(distance or 0.0)))
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                filename=filename,
                page=chunk.page or 1,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                similarity_score=round(score, 4),
            )
        )

    logger.info(
        "Document chunks retrieved",
        tenant_id=str(tenant_id),
        query=query[:60],
        chunks_count=len(retrieved),
    )
    return retrieved


def search_chunks_sync(
    db: Session,
    tenant_id: uuid.UUID,
    query: str,
    limit: int = 5,
) -> list[RetrievedChunk]:
    """Synchronous tenant-filtered vector search for background tasks and offline evaluation."""
    if not query.strip():
        return []

    query_vector = embed_query(query)
    dist = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")

    stmt = (
        select(DocumentChunk, Document.filename, dist)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.tenant_id == tenant_id,
            Document.tenant_id == tenant_id,
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(dist)
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    retrieved = []
    for chunk, filename, distance in rows:
        score = max(0.0, min(1.0, 1.0 - float(distance or 0.0)))
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                filename=filename,
                page=chunk.page or 1,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                similarity_score=round(score, 4),
            )
        )

    return retrieved
