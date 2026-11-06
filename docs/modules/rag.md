# Module Specification: Document Parsing, Chunking & Embeddings (rag.md)

## 1. Purpose
The RAG pipeline is responsible for transforming raw financial files (PDF and CSV invoices, purchase orders, contracts) into structured accounting data and dense vector representations. It extracts structured invoice metadata (vendor, invoice number, date, amount, GSTIN), chunks document text with preserved page boundaries, generates 1536-dimensional embeddings, and stores chunks with strict `tenant_id` isolation and HNSW vector indexing in PostgreSQL (`pgvector`).

## 2. Files
- `app/models/chunk.py`: SQLAlchemy table definition for `document_chunks` with an HNSW cosine index on `embedding`.
- `app/schemas/chunk.py`: Pydantic response models for chunks inspection.
- `app/rag/parser.py`: PDF parser (using `pypdf` with heuristic regex extraction) and CSV parser.
- `app/rag/chunker.py`: Text chunker wrapping `RecursiveCharacterTextSplitter` with page number tracking.
- `app/rag/embedder.py`: Batch vector embedding provider with OpenAI-compatible API support and deterministic offline fallback.
- `app/routes/invoices.py`: FastAPI endpoints for listing extracted invoices (`GET /invoices`, `GET /invoices/{id}`).
- `app/services/invoice_service.py`: Encapsulated database queries for invoices filtered by `tenant_id`.

## 3. Inputs and Outputs

### Extracted Invoice Data
- **Input:** Raw binary bytes of uploaded PDF or CSV file.
- **Output (`ExtractedInvoiceData`):**
  - `vendor_name`: String (e.g., "Sharma Traders")
  - `invoice_number`: String (e.g., "INV-1042")
  - `total_amount`: Decimal (e.g., `Decimal("118000.00")` stored as `NUMERIC(18, 2)`)
  - `invoice_date`: Date (e.g., `2026-08-12`)
  - `vendor_gstin`: String (e.g., "07AAAAA0000A1Z5")

### Document Chunks
- **Chunk Size:** 600 characters with 60-character overlap.
- **Output (`DocumentChunk` row):**
  - `id`: UUID
  - `tenant_id`: UUID
  - `document_id`: UUID
  - `chunk_index`: Integer (0-based sequential ordering)
  - `page`: Integer (1-based source page number)
  - `text`: Chunk text snippet
  - `embedding`: Vector(1536)

## 4. Failure Cases
- **Unextractable/Scanned PDF:** When an invoice PDF is a pure scanned image without text layers, regex extraction yields `None`. Document chunks are stored if any OCR/text exists; the document status is set to `done`, and invoice extraction falls back to manual or later OCR phases.
- **Malformed Numeric Amount:** Unparseable currency strings are safely discarded to avoid financial data corruption.
- **Embedding API Outage:** When external embedding APIs are unreachable or offline, the embedder automatically falls back to deterministic unit-normalized 1536d vectors, preventing worker task crashes.

## 5. How to Test It
Run automated unit and integration tests:
```bash
docker compose exec api python -m unittest tests/test_rag.py -v
```

Manual API inspection:
```bash
# View extracted invoices
curl -s http://localhost:8000/invoices -H "Authorization: Bearer <token>"

# View chunks for an uploaded document
curl -s http://localhost:8000/documents/<doc_id>/chunks -H "Authorization: Bearer <token>"
```

Interactive Web Dashboard:
Visit `http://localhost:8000/ui` to upload invoices, view the extracted invoices table, and click "Chunks" to inspect the chunk texts and pgvector status.

## 6. Known Limits
- Regex extraction targets standard invoice patterns; complex multi-column or scanned invoices will be upgraded with OCR and LLM-assisted extraction in Phase 2.
- Vector dimension is currently locked to 1536 (`text-embedding-3-small`). Changing embedding models requires an Alembic schema update.
