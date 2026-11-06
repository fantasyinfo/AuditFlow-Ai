# AuditFlow AI — Antigravity Agent Guidelines & Rules

> This rules file defines the non-negotiable architectural constraints, coding standards, security guardrails, and behavioral guidelines for developing the **AuditFlow AI** platform. Every agent working in this repository must strictly adhere to these rules.

---

## 1. Project Overview & Role
AuditFlow AI is an automated Accounts Payable (AP) audit and fraud detection platform. It ingests invoices, POs, and contracts asynchronously, extracts key financial data, runs deterministic audit rules, stores chunked document embeddings in PostgreSQL (`pgvector`), and enables finance teams to query documents and findings via a **strictly read-only** LangChain agent with mandatory citations.

---

## 2. Non-Negotiable Core Invariants

### 2.1 Multi-Tenancy Isolation
- **Tenant Scoping:** Every domain table (documents, chunks, invoices, purchase orders, findings, audit logs, idempotency keys) MUST contain a `tenant_id` foreign key column indexed with `created_at`.
- **Query Filtering:** Every database read, update, and delete query MUST explicitly filter by `tenant_id`. No query may cross tenant boundaries under any circumstances.
- **Tenant Context:** FastAPI dependencies (`get_current_tenant`, `get_current_user`) must supply the verified `tenant_id` extracted from the JWT token.

### 2.2 Financial Data Integrity
- **Currency Representation:** ALL monetary amounts (invoice totals, line items, PO amounts, tax values) MUST be represented as `Decimal` in Python and `NUMERIC(18, 2)` in PostgreSQL/SQLAlchemy.
- **Forbidden Types:** NEVER use `float` or `double` for money or accounting calculations.

### 2.3 Database Sessions: Async vs. Sync
- **FastAPI Layer:** Use `asyncpg` with asynchronous SQLAlchemy sessions (`AsyncSession`) for all API endpoints.
- **Celery Worker Layer:** Celery worker processes execute synchronously. They MUST use `psycopg2-binary` with synchronous SQLAlchemy sessions (`Session`). Do NOT create event loops inside Celery worker tasks.

### 2.4 Agent Safety: Strictly Read-Only
- The LangChain agent (`app/agent/`) and its tools (`app/agent/tools.py`) are **strictly read-only**.
- Tools may ONLY query vector embeddings, fetch document text, retrieve invoices, or list findings.
- Tools MUST NEVER insert, update, or delete database rows or files.
- Agent outputs MUST include explicit citations (`[filename.pdf p.X]`, `[finding #ID]`). If information is absent from retrieved context, the agent must respond: *"I could not find this in your documents."*

---

## 3. Architecture & Clean Layer Separation

Follow the strict layered architecture:
```
Routes (app/routes/)          -> Validates request, handles HTTP, calls Services. No business logic.
Services (app/services/)      -> Encapsulates business logic, orchestrates DB and Queue.
Rules (app/rules/)            -> Pure deterministic audit detection functions.
Worker (app/worker/)          -> Celery tasks that invoke Services and Rules.
RAG Pipeline (app/rag/)       -> Document parser, chunker, embedder, and tenant-scoped retriever.
Agent (app/agent/)            -> Read-only tool-calling agent with strict citation prompts.
Models & Schemas (app/models/ & app/schemas/) -> SQLAlchemy 2.0 models & Pydantic v2 schemas.
```

- **No SQL in Routes:** Route handlers must only call service functions and return Pydantic response models.
- **Storage Abstraction:** File uploads must go through a storage service abstraction (`LocalStorageBackend` today, swappable for S3/MinIO later).

---

## 4. Coding Conventions & Style

- **Python Version:** Target Python 3.12+.
- **Type Annotations:** Full type hints on all function arguments and return values (`def func(param: str) -> bool:`).
- **Naming Conventions:** Plain, intuitive snake_case names: `save_upload`, `parse_pdf`, `check_duplicate`, `run_rules`.
- **Pydantic v2:** Use Pydantic v2 idioms (`model_validate`, `field_validator`, `BaseModel.model_dump()`).
- **Rule Design Pattern:** Each detection rule must reside in its own file (`app/rules/<rule_name>.py`) and expose a callable:
  ```python
  def check_<rule_name>(invoice: Invoice, db: Session, **kwargs) -> Optional[FindingCreate]: ...
  ```
- **Error Handling:** Return proper HTTP status codes (400 for bad payloads, 401/403 for auth/tenancy errors, 404 for missing entities, 409 for conflicts/duplicates, 422 for unprocessable files).

---

## 5. Security & Privacy Guardrails

- **Authentication:** Use direct `bcrypt` (`bcrypt.hashpw`, `bcrypt.checkpw`) for password hashing. Do not rely on deprecated `passlib` wrappers with Python 3.12.
- **Token Hygiene:** Sign JWTs with a strong secret key, algorithm HS256, and enforce expiration.
- **Log Hygiene:** NEVER log passwords, JWT tokens, API keys, authorization headers, or full raw invoice texts in application or Celery logs. Use `structlog` for structured, sanitized JSON logging.
- **PII / LLM Safety:** Redact sensitive identity and banking details (PAN, bank account numbers) where necessary before dispatching prompts to third-party LLM providers.
- **Idempotency:** Write endpoints (`POST /documents`) must honor the `Idempotency-Key` header and store responses in `idempotency_keys` table to prevent duplicate ingestion.

---

## 6. Dependency & Version Management

- **Strict Locking:** NEVER install or add dependencies with floating versions (e.g. `fastapi>=0.100`). Always lock exact versions (`fastapi==0.115.6`).
- **Sync Changes:** Whenever modifying `requirements.txt`, verify compatibility against `Dockerfile` and update `requirements-dev.txt` accordingly.

---

## 7. Documentation & Testing Policy

- **Synchronous Documentation:** When implementing or updating a module, update its corresponding specification in `docs/modules/<module_name>.md` in the same step.
- **Unit Tests for Rules:** Every rule in `app/rules/` must have automated unit tests covering both positive (finding generated) and negative (valid invoice passes) scenarios.
- **Multi-Tenant Isolation Tests:** Every new endpoint must have a test verifying that Tenant B cannot access Tenant A's documents, invoices, or findings.

---

## 8. Progress Tracking & Web Testing UI

- **Checklist Verification:** Keep `AuditFlow AI MVP Project Plan.md` updated after each milestone. Explicitly mark completed and verified deliverables with `[x] (tested & verified)`.
- **Web Testing Dashboard:** Maintain a lightweight, self-contained web testing UI served directly by FastAPI (e.g. at `/ui` or `/dashboard`). As each phase is built (Auth, Documents, Invoices, Findings, Agent), update the UI so the user can interactively test the entire flow in the browser without needing cURL or Postman.


