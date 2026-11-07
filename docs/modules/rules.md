# Module Specification: Rules Engine (rules.md)

## 1. Purpose
The AuditFlow Rules Engine evaluates invoices deterministically to identify potential billing anomalies, duplicate submissions, contract/PO discrepancies, tax non-compliance, and unusual expenditure spikes. Every rule is implemented as a pure, testable function that inspects an invoice within its tenant boundary and returns a `FindingCreate` object if an anomaly is identified.

## 2. Files
- `app/models/finding.py`: SQLAlchemy model for the `findings` table with multi-tenant foreign keys, composite indexes on `(tenant_id, created_at)` and `(tenant_id, invoice_id)`.
- `app/schemas/finding.py`: Pydantic request/response schemas (`FindingCreate`, `FindingUpdate`, `FindingResponse`, `FindingListResponse`).
- `app/services/finding_service.py`: Encapsulated database operations for querying and updating findings within tenant scope.
- `app/routes/findings.py`: FastAPI endpoints (`GET /findings`, `GET /findings/{id}`, `PATCH /findings/{id}`).
- `app/rules/run_rules.py`: Orchestrator that executes all active deterministic rules on a newly extracted or updated invoice.
- `app/rules/duplicate_invoice.py`: Checks for duplicate invoice numbers or identical vendor + amount + date collisions.
- `app/rules/amount_mismatch.py`: Compares invoice total amount against linked purchase order total.
- `app/rules/missing_evidence.py`: Flags invoices with total amount exceeding ₹10,000 lacking a linked purchase order.
- `app/rules/gstin_check.py`: Validates Indian 15-character GSTIN checksum and format structure.
- `app/rules/unusual_amount.py`: Identifies invoices where the total exceeds 2.5× the vendor's historical average billing.
- `tests/test_rules.py`: Complete test suite covering positive and negative evaluation cases for every rule.

## 3. Implemented Rules & Inputs/Outputs

### 3.1 Duplicate Invoice (`check_duplicate_invoice`)
- **Criteria:** Same vendor and invoice number (`uq_invoices_tenant_vendor_number`), OR same vendor, amount, and invoice date on a different invoice.
- **Severity:** `critical`

### 3.2 Amount Mismatch (`check_amount_mismatch`)
- **Criteria:** Linked PO total amount differs from invoice total amount by more than ₹1.00 tolerance.
- **Severity:** `high`

### 3.3 Missing Evidence (`check_missing_evidence`)
- **Criteria:** Invoice total > ₹10,000.00 has no linked `po_id` or referenced PO document.
- **Severity:** `medium`

### 3.4 GSTIN Check (`check_gstin_format`)
- **Criteria:** Vendor GSTIN fails India GST format regex (`^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`).
- **Severity:** `high`

### 3.5 Unusual Amount (`check_unusual_amount`)
- **Criteria:** Invoice total > ₹10,000.00 and exceeds 2.5× vendor historical average (requires at least 3 historical invoices).
- **Severity:** `medium`

### 3.6 Tenant-Custom Rules (`custom_rule_evaluator`)
- **Criteria:** Dynamic tenant-defined threshold or condition evaluated per invoice.
- **Supported Rule Types:**
  - `amount_threshold`: Compares `total_amount` against threshold using operators (`gt`, `gte`, `lt`, `lte`, `eq`, `neq`).
  - `vendor_match`: Checks `vendor_name` against a pattern using `contains`, `not_contains`, `eq`, or `regex`.
  - `missing_field`: Verifies presence of mandatory fields (`vendor_gstin`, `invoice_number`, `invoice_date`, `po_id`).
  - `date_check`: Flags weekend invoices (`operator: "weekend"`) or future invoice dates (`operator: "future"`).
  - `keyword_check`: Scans invoice metadata/notes for suspicious terms (e.g. "gift", "facilitation", "consulting fee").
- **Dynamic Formatting:** Findings dynamically interpolate `{invoice_number}`, `{vendor_name}`, `{field_name}`, `{field_value}`, and `{threshold}` into custom user-configured explanation templates.
- **Severity:** User-configurable (`low`, `medium`, `high`, `critical`).

## 4. Failure Cases
- **No PO Found:** Handled gracefully by `missing_evidence` without raising database foreign key exceptions.
- **Division by Zero:** Guarded in `unusual_amount` by requiring count $\ge 3$ and historical average $> 0$.
- **Precision Truncation:** Monetary comparisons strictly employ Python `Decimal` with quantized representation to eliminate floating point rounding inaccuracies.

## 5. How to Test It
Execute the unit test suite inside the container:
```bash
docker compose exec api python -m unittest tests/test_rules.py -v
```

Manual API inspection:
```bash
# List all open findings
curl -s http://localhost:8000/findings -H "Authorization: Bearer <token>"

# Confirm a finding
curl -s -X PATCH http://localhost:8000/findings/<finding_id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "confirmed", "review_notes": "Verified duplicate submission by vendor."}'
```

Interactive Web Dashboard:
Visit `http://localhost:8000/ui` to inspect detected audit findings, filter by status or rule type, and confirm or dismiss findings interactively.

## 6. Known Limits
- Historical average calculation uses a simple arithmetic mean; Phase 2 will introduce sliding time windows (last 90 days) and standard deviation outlier detection ($Z$-score).
- Cross-tenant duplicate detection is strictly prevented by design; multi-entity intercompany duplicates will require explicit group tenant authorization.
