# Module Specification: Immutable Audit Log (audit_log.md)

## 1. Purpose
The Audit Log module maintains an append-only, tamper-evident record of all security-sensitive and compliance actions within AuditFlow AI. Any status change on an audit finding (such as confirmation or dismissal by a finance reviewer), document upload, or system action records the actor's user ID, tenant ID, entity type, entity ID, action name, and before/after state diffs.

## 2. Files
- `app/models/audit_log.py`: SQLAlchemy table definition for `audit_log` with composite index on `(tenant_id, created_at)` and indexed `(tenant_id, entity, entity_id)`.
- `app/schemas/audit_log.py`: Pydantic schemas for reading audit log entries (`AuditLogResponse`, `AuditLogListResponse`).
- `app/services/audit_service.py`: Service functions `record_audit_event` and `list_audit_logs`.
- `app/routes/findings.py`: Injects audit logging whenever a reviewer confirms or dismisses a finding.
- `app/routes/audit_logs.py` / `app/routes/ui.py`: Provides audit log viewing endpoints and visual timeline in the Web Dashboard.

## 3. Schema & Data Model
- `id`: UUID (Primary Key)
- `tenant_id`: UUID (Foreign Key -> `tenants.id`, NOT NULL)
- `user_id`: UUID (Foreign Key -> `users.id`, nullable for system automated actions)
- `action`: String (e.g., `finding.confirmed`, `finding.dismissed`, `finding.created`, `document.uploaded`)
- `entity`: String (e.g., `finding`, `document`, `invoice`)
- `entity_id`: UUID (ID of the affected entity)
- `before_state`: JSON / Dictionary (previous field values)
- `after_state`: JSON / Dictionary (updated field values)
- `created_at`: DateTime (UTC, immutable)

## 4. Failure Cases
- **Missing User Context:** When an action is performed by background workers (Celery), `user_id` is set to `None` and the action is recorded with system context without crashing.
- **Serialization Failures:** All `before_state` and `after_state` payloads are pre-sanitized (e.g., converting `Decimal` to string or float representation) to prevent JSON serialization errors in PostgreSQL `JSONB` columns.

## 5. How to Test It
Verify via API:
```bash
# Retrieve recent audit log entries for current tenant
curl -s http://localhost:8000/audit-logs -H "Authorization: Bearer <token>"
```

Interactive Web Dashboard:
Visit `http://localhost:8000/ui`, review a finding, click **Confirm** or **Dismiss**, and verify the update immediately appears under the **Audit Trail** panel with timestamps and before/after status.

## 6. Known Limits
- In Phase 1 (MVP), audit logs are stored in standard append-only PostgreSQL tables. Phase 2 will introduce cryptographic hash-chaining (Merkle chaining) where each log entry includes `sha256(prev_hash + entry_data)` to guarantee mathematical non-repudiation.
