# Module Specification: Background Worker & Tasks (worker.md)

## 1. Purpose
The AuditFlow Worker layer offloads CPU-intensive document parsing, OCR text extraction, chunking, semantic vector embedding generation, invoice record structuring, and deterministic audit rules evaluation to background processes. By delegating asynchronous tasks via Celery and Redis, the user-facing FastAPI application maintains sub-millisecond response times and guarantees high request ingestion throughput.

## 2. Files
- `app/worker/celery_app.py`: Celery instance configuration, Redis broker/backend connections, and JSON serialization.
- `app/worker/tasks.py`: Celery task definitions including `process_document`.
- `app/database.py`: Dedicated synchronous SQLAlchemy session factory (`SyncSessionLocal` via `psycopg2-binary`) specifically for Celery workers to prevent event loop collisions.
- `Dockerfile.worker`: Containerization profile running Celery with dedicated concurrency.
- `docker-compose.yml`: Service orchestrator mounting worker service (`worker`) against Redis and PostgreSQL.

## 3. Asynchronous Workflow
1. **Task Dispatch:** FastAPI route `POST /documents` receives the file, stores it via `LocalStorageBackend`, writes a `PENDING` record to PostgreSQL, and calls `process_document.delay(document_id, tenant_id)`.
2. **Document Ingestion & Status Update:** Celery worker retrieves the task, updates document status to `PROCESSING`, and reads binary content from disk.
3. **Parsing & Chunking:** Worker runs `parse_document()` (PDF text extraction via `pdfplumber` or structured CSV extraction) and splits content into overlapping 500-token chunks with `chunk_document()`.
4. **Vector Embedding:** Embeddings are generated in batches using `embed_texts()` and stored in the `document_chunks` table with `pgvector` indexing.
5. **Invoice Structuring:** If document represents an invoice, an `invoices` row is persisted with `Decimal` amounts.
6. **Rule Evaluation:** Worker evaluates all active built-in audit checks and tenant-configured custom rules synchronously via `run_all_rules(invoice, session)` and commits findings.
7. **Completion / Error Handling:** Document status is transitioned to `DONE`. In case of unrecoverable failure, status becomes `FAILED` with `error_message` captured.

## 4. Concurrency & Scaling
- **Concurrency Model:** Sync processes using `psycopg2-binary` connection pooling.
- **Horizontal Scaling:** Workers are stateless. Additional worker containers can be scaled on demand:
  ```bash
  docker compose up -d --scale worker=4
  ```
- **Retries & Fault Tolerance:** `process_document` is decorated with `bind=True, max_retries=3`. Transient network failures to LLM/embedding endpoints trigger Celery automatic retries.

## 5. How to Test & Monitor
Check worker logs in real time:
```bash
docker compose logs -f worker
```

Inspect Redis queue length:
```bash
docker compose exec redis redis-cli llen celery
```

Verify end-to-end task execution in test suite:
```bash
docker compose exec api python -m unittest tests/test_e2e_pipeline.py -v
```

## 6. Known Limits
- Celery worker currently writes to local volume storage (`./storage/uploads`); production deployment will swap this for MinIO or AWS S3 (`S3StorageBackend`).

