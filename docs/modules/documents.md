# Module Specification: Document Ingestion & Queue (documents.md)

## 1. Purpose
The Document Ingestion module provides high-throughput, non-blocking asynchronous intake of financial documents (invoices, purchase orders, and contracts in PDF and CSV format). It validates payloads, persists files to a pluggable storage backend, stores document metadata, enforces request idempotency, and immediately dispatches background parsing tasks to Celery via Redis with a `202 Accepted` response.

## 2. Files
- `app/models/document.py`: SQLAlchemy table definition for `documents` with status tracking (`queued`, `processing`, `done`, `failed`).
- `app/models/idempotency.py`: SQLAlchemy table for deduplicating API requests via `(tenant_id, key)`.
- `app/models/invoice.py`: Domain model for extracted invoice records.
- `app/models/purchase_order.py`: Domain model for purchase orders with monetary amounts stored as `NUMERIC(18, 2)`.
- `app/schemas/document.py`: Pydantic request/response schemas for document metadata and upload acknowledgment.
- `app/services/storage.py`: Storage abstraction interface (`StorageBackend`) and `LocalStorageBackend` implementation.
- `app/services/idempotency_service.py`: Service checking and storing cached responses for idempotent operations.
- `app/services/document_service.py`: Core business logic for file validation, storage, and Celery task dispatch.
- `app/routes/documents.py`: FastAPI routes exposing `POST /documents`, `GET /documents/{id}`, and `GET /documents`.
- `app/worker/tasks.py`: Celery background tasks executing synchronous document status transitions.

## 3. Inputs and Outputs

### Upload Document (`POST /documents`)
- **Headers:**
  - `Authorization: Bearer <token>`
  - `Idempotency-Key: <unique_client_key>` (Optional)
- **Form Data:**
  - `file`: Multipart file binary (`.pdf` or `.csv`, max 10MB)
  - `doc_type`: String (`invoice`, `purchase_order`, `contract`, `other`)
- **Output (`202 Accepted`):**
  ```json
  {
    "id": "420b9e76-4ed2-456e-944a-b5459105914b",
    "filename": "invoice_1042.csv",
    "status": "queued",
    "message": "Document accepted and queued for background processing."
  }
  ```

### Get Document Status (`GET /documents/{id}`)
- **Header:** `Authorization: Bearer <token>`
- **Output (`200 OK`):**
  ```json
  {
    "id": "420b9e76-4ed2-456e-944a-b5459105914b",
    "tenant_id": "624c6a88-02e8-409c-b4b4-3177d9ef5a59",
    "filename": "invoice_1042.csv",
    "type": "invoice",
    "status": "done",
    "storage_path": "uploads/624c6a88-02e8-409c-b4b4-3177d9ef5a59/...",
    "created_by": "19dcfebf-37e9-4a67-b55d-6485f0ff8931",
    "error_message": null,
    "created_at": "2026-11-06T10:04:14.781624Z"
  }
  ```

## 4. Failure Cases
- **Unsupported File Format:** Uploading files other than `.pdf` or `.csv` returns `422 Unprocessable Entity`.
- **Payload Exceeds Limit:** Files larger than `MAX_UPLOAD_MB` (10MB) return `413 Request Entity Too Large`.
- **Cross-Tenant Access:** Querying a document belonging to another tenant returns `404 Not Found` (strict data isolation).
- **Worker Failure:** If parsing fails in Celery, document status is flipped to `failed` and `error_message` is populated.

## 5. How to Test It
Run automated integration and multi-tenancy isolation tests:
```bash
docker compose exec api python -m unittest tests/test_documents.py -v
```

Interactive Web Dashboard:
Open your browser at `http://localhost:8000/ui` to upload files, test idempotency, and watch real-time queue status transitions.

## 6. Known Limits
- Files are saved to local volume (`/data/uploads`); S3/MinIO cloud adapter will be added in Phase 2.
- Worker currently transitions status from `queued` $\to$ `processing` $\to$ `done`; text chunking and vector embeddings are integrated in Day 3.
