import uuid
import structlog
from app.database import SyncSessionLocal
from app.models.document import Document, DocumentStatus
from app.worker.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.worker.tasks.process_document", bind=True, max_retries=3)
def process_document(self, document_id: str, tenant_id: str) -> dict[str, str]:
    """Background task to process an uploaded document and transition status."""
    session = SyncSessionLocal()
    try:
        doc_uuid = uuid.UUID(document_id)
        tenant_uuid = uuid.UUID(tenant_id)

        doc = session.query(Document).filter(
            Document.id == doc_uuid,
            Document.tenant_id == tenant_uuid,
        ).first()

        if not doc:
            logger.error(
                "Document not found for processing",
                document_id=document_id,
                tenant_id=tenant_id,
            )
            return {"status": "not_found", "document_id": document_id}

        # Step 1: Mark as processing
        doc.status = DocumentStatus.PROCESSING.value
        session.commit()

        # Day 2 milestone: Flip status to done to verify Celery queue drain
        doc.status = DocumentStatus.DONE.value
        session.commit()

        logger.info(
            "Document processing completed successfully",
            document_id=document_id,
            tenant_id=tenant_id,
        )
        return {"status": "done", "document_id": document_id}
    except Exception as exc:
        session.rollback()
        logger.exception("Document processing failed", exc=exc, document_id=document_id)
        # Attempt to mark document as failed
        try:
            doc = session.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
            if doc:
                doc.status = DocumentStatus.FAILED.value
                doc.error_message = str(exc)[:1000]
                session.commit()
        except Exception:
            session.rollback()
        raise exc
    finally:
        session.close()
