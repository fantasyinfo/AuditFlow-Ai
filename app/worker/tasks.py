from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.process_document")
def process_document(document_id: str) -> dict[str, str]:
    """Placeholder task for document processing pipeline."""
    return {"document_id": document_id, "status": "queued"}
