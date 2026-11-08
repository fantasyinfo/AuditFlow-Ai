import os
import uuid
from typing import Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.document import Document, DocumentStatus, DocumentType
from app.schemas.document import DocumentRead, DocumentUploadResponse
from app.services.storage import storage_backend
from app.worker.tasks import process_document

settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".csv"}


class DocumentService:
    @staticmethod
    async def upload_document(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        file: UploadFile,
        doc_type: str = DocumentType.INVOICE.value,
        project_id: Optional[uuid.UUID] = None,
    ) -> DocumentUploadResponse:
        filename = file.filename or "unnamed_document"
        _, ext = os.path.splitext(filename.lower())

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file format '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        content = await file.read()
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed upload size of {settings.MAX_UPLOAD_MB}MB.",
            )

        # Save to storage backend abstraction
        storage_path = await storage_backend.save_file(
            tenant_id=tenant_id,
            filename=filename,
            content=content,
        )

        # Persist Document row
        doc = Document(
            tenant_id=tenant_id,
            filename=filename,
            type=doc_type,
            status=DocumentStatus.QUEUED.value,
            storage_path=storage_path,
            created_by=user_id,
            project_id=project_id,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        # Enqueue background task to Celery
        process_document.delay(str(doc.id), str(tenant_id))

        return DocumentUploadResponse(
            id=doc.id,
            filename=doc.filename,
            status=DocumentStatus(doc.status),
            message="Document accepted and queued for background processing.",
        )

    @staticmethod
    async def get_document(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Optional[Document]:
        """Fetch document strictly filtered by tenant_id."""
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
        result = await session.execute(query)
        return result.scalars().first()

    @staticmethod
    async def list_documents(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        """List documents strictly filtered by tenant_id."""
        query = (
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_document(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> bool:
        """Delete document, related file on disk, and cascade DB rows strictly within tenant."""
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
        result = await session.execute(query)
        doc = result.scalars().first()
        if not doc:
            return True

        if doc.storage_path and os.path.exists(doc.storage_path):
            try:
                os.remove(doc.storage_path)
            except OSError:
                pass

        await session.delete(doc)
        await session.commit()
        return True

