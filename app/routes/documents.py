import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.chunk import DocumentChunk
from app.schemas.auth import CurrentUser
from app.schemas.chunk import ChunkRead
from app.schemas.document import DocumentRead, DocumentUploadResponse
from app.services.document_service import DocumentService
from app.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload invoice or document for asynchronous processing",
)
async def upload_document(
    file: Annotated[UploadFile, File(description="Invoice, PO, or Contract (PDF or CSV)")],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    doc_type: Annotated[str, Form(description="Document type")] = "invoice",
    project_id: Annotated[Optional[uuid.UUID], Form(description="Associated Project ID")] = None,
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    """Accept and store document, enqueue processing task, and return 202 immediately."""
    # Check idempotency
    if idempotency_key:
        cached = await IdempotencyService.get_response(
            session=session,
            tenant_id=current_user.tenant_id,
            key=idempotency_key,
        )
        if cached:
            return JSONResponse(
                status_code=cached["status_code"],
                content=cached["body"],
                headers={"X-Cache-Lookup": "HIT"},
            )

    response_data = await DocumentService.upload_document(
        session=session,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        file=file,
        doc_type=doc_type,
        project_id=project_id,
    )

    body = response_data.model_dump(mode="json")
    if idempotency_key:
        await IdempotencyService.record_response(
            session=session,
            tenant_id=current_user.tenant_id,
            key=idempotency_key,
            status_code=status.HTTP_202_ACCEPTED,
            body=body,
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=body,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    summary="Get document processing status and metadata",
)
async def get_document(
    document_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentRead:
    """Fetch status for an uploaded document, strictly scoped to caller's tenant."""
    doc = await DocumentService.get_document(
        session=session,
        tenant_id=current_user.tenant_id,
        document_id=document_id,
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return DocumentRead.model_validate(doc)


@router.get(
    "/{document_id}/chunks",
    response_model=list[ChunkRead],
    summary="Get extracted text chunks for a document",
)
async def get_document_chunks(
    document_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChunkRead]:
    """Retrieve all chunks belonging to a document, strictly scoped to caller's tenant."""
    from sqlalchemy import select

    query = (
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.tenant_id == current_user.tenant_id,
        )
        .order_by(DocumentChunk.chunk_index.asc())
    )
    result = await session.execute(query)
    chunks = result.scalars().all()
    return [ChunkRead.model_validate(c) for c in chunks]


@router.get(
    "",
    response_model=list[DocumentRead],
    summary="List uploaded documents for the tenant",
)
async def list_documents(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
) -> list[DocumentRead]:
    """Retrieve tenant's documents sorted by newest first."""
    docs = await DocumentService.list_documents(
        session=session,
        tenant_id=current_user.tenant_id,
        limit=limit,
        offset=offset,
    )
    return [DocumentRead.model_validate(d) for d in docs]


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an uploaded document and its chunks",
)
async def delete_document(
    document_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete document row, underlying file, and vector chunks strictly within caller's tenant."""
    await DocumentService.delete_document(
        session=session,
        tenant_id=current_user.tenant_id,
        document_id=document_id,
    )

