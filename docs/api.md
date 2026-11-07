# AuditFlow AI — REST API Reference Specification

Base URL: `http://localhost:8000`  
Interactive OpenAPI UI: `http://localhost:8000/docs`

---

## 1. Authentication & Multi-Tenancy

Every request to a protected endpoint must supply a verified JWT Bearer token:
```http
Authorization: Bearer <jwt_access_token>
```
The token encapsulates `tenant_id`, `user_id`, and `role`.

### Endpoints
- `POST /auth/register`: Create a new tenant and administrator account.
- `POST /auth/login`: Authenticate and receive a JWT access token.
- `GET /auth/me`: Get profile and tenant isolation context.

---

## 2. Document Ingestion Queue

- `POST /documents`: Upload commercial PDF or CSV.
  - Headers: `Idempotency-Key` (optional, caches response to prevent duplicate ingestion).
  - Form Data: `file` (binary), `document_type` (`invoice` | `quotation` | `agreement` | `purchase_order` | `other`).
  - Response: `202 Accepted` with document UUID and queue status `queued`.
- `GET /documents`: List ingested documents for the tenant.
- `GET /documents/{id}/chunks`: Retrieve 1536-dimensional pgvector chunk embeddings and page breakdown.

---

## 3. Commercial Records (Invoices & Metadata)

- `GET /invoices`: List structured financial records extracted from documents.
- `GET /invoices/{id}`: Retrieve detailed record including line items and associated findings.

---

## 4. Audit Findings & Fraud Investigation

- `GET /findings`: List detected rule violations.
  - Query parameters: `status` (`open` | `confirmed` | `dismissed`), `rule`, `limit`, `offset`.
- `PATCH /findings/{id}`: Human auditor review action.
  - Payload: `{"status": "confirmed" | "dismissed", "notes": "Reason"}`.
  - Writes an immutable record with before/after state diff to the audit trail.
- `GET /audit-logs`: Query immutable compliance log trail.

---

## 5. Audit Rules & Custom Rule Builder

- `GET /rules`: List all active rules (both the 5 built-in rules and tenant custom rules).
- `GET /rules/custom`: List tenant custom rules.
- `POST /rules/custom`: Create a custom policy rule.
  - Fields: `name`, `code`, `severity`, `rule_type`, `field_to_evaluate`, `operator`, `threshold_value`, `reason_template`, `is_active`.
- `PATCH /rules/custom/{id}`: Update or activate/deactivate rule.
- `DELETE /rules/custom/{id}`: Delete custom rule.

---

## 6. AI Audit Assistant (Google AI Studio Gemini + RAG)

- `POST /agent/ask`: Plain-language natural language query.
  - Payload: `{"query": "Are there any duplicate invoices or PO mismatches?"}`
  - Response:
    ```json
    {
      "query": "Are there any duplicate invoices?",
      "answer": "Yes, invoice INV-1042-DUP from Sharma Traders is flagged as a duplicate...",
      "citations": ["[invoice_1042.pdf p.1]", "[finding #885fab1e]"],
      "answered_from_sources": true
    }
    ```

---

## 7. Metrics & Observability

- `GET /health`: Liveness and database connectivity.
- `GET /metrics`: Prometheus application and HTTP request latency metrics.
