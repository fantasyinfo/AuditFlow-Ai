# Module Specification: Projects & Financial Reconciliation (projects.md)

## 1. Purpose
The Projects & Financial Reconciliation module organizes documents, legal contracts, purchase orders, and invoices into discrete vendor engagement workspaces. It enables finance and audit teams to establish baseline quotation budgets, enforce maximum contract caps, deconstruct invoices by removing GST to inspect pure service/goods costs, calculate over-logged or under-logged expenditure percentages, and track paid disbursements versus remaining contract balances.

## 2. Files
- `app/models/project.py`: SQLAlchemy `Project` model with multi-tenant foreign keys, baseline budget, agreed GST percentage, over-billing tolerance threshold, and single invoice caps.
- `app/schemas/project.py`: Pydantic v2 schemas (`ProjectCreate`, `ProjectUpdate`, `ProjectResponse`, `ProjectSummaryItem`, `ProjectReconciliationResponse`, `PaymentRecordRequest`).
- `app/services/project_service.py`: Encapsulates quotation calculations, net base price derivation, over/under-logged variance formulas, payment recording, and tenant-scoped database queries.
- `app/routes/projects.py`: FastAPI endpoints (`GET /projects`, `POST /projects`, `GET /projects/{id}`, `GET /projects/{id}/reconciliation`, `PATCH /projects/{id}`, `DELETE /projects/{id}`, `POST /projects/{id}/invoices/{id}/payments`, `POST /projects/{id}/link-invoice/{id}`).
- `app/rules/project_rules.py`: Deterministic audit rules evaluating `project_overbudget` and `project_cap_exceeded`.
- `frontend/src/modules/projects/ProjectsModule.jsx`: Project workspace UI with live burn-rate gauges, quotation caps, and 1-click presets.
- `frontend/src/modules/reconciliation/ReconciliationModule.jsx`: Interactive reconciliation view with GST removal tool, TDS simulator, and invoice payment recording.
- `tests/test_projects.py`: Automated unit, integration, multi-tenancy isolation, and reconciliation math tests.

## 3. Financial Reconciliation Math & Logic

### 3.1 Quotation Baseline Computation
$$\text{Quoted Net (Ex-GST)} = \frac{\text{Quoted Gross}}{1 + \frac{\text{GST Rate } \%}{100}}$$
$$\text{Quoted GST} = \text{Quoted Gross} - \text{Quoted Net}$$

### 3.2 Invoice Dissection & GST Removal
For any invoice with total amount $T$ and GST rate $R$:
$$\text{Net Amount (Goods/Services)} = \frac{T}{1 + \frac{R}{100}}$$
$$\text{GST Component (Tax Claimed)} = T - \text{Net Amount}$$

### 3.3 Over-Logged & Under-Logged Expenditure
$$\text{Variance Amount} = \text{Total Invoiced Gross} - \text{Quoted Gross}$$
$$\text{Variance } \% = \left(\frac{\text{Variance Amount}}{\text{Quoted Gross}}\right) \times 100$$
$$\text{Burn Rate } \% = \left(\frac{\text{Total Invoiced Gross}}{\text{Quoted Gross}}\right) \times 100$$
- If $\text{Total Invoiced} > \text{Quoted Gross}$, status is **Over-Logged** ($\text{Over Amount} = \text{Variance}$).
- If $\text{Variance } \% > \text{Tolerance } \%$, an automated `project_overbudget` audit finding is raised.

### 3.4 Payment Tracking ("Paid vs Left")
$$\text{Remaining Balance to Pay Under Contract} = \text{Quoted Gross} - \text{Total Disbursed (Paid)}$$
$$\text{Uncommitted Budget for Future Invoices} = \max(0, \text{Quoted Gross} - \text{Total Invoiced Gross})$$

## 4. Failure Cases
- **Duplicate Project Code:** Enforced via `uq_projects_tenant_code` constraint; returns `HTTP 409 Conflict`.
- **Negative Payment Recording:** Schema validation rejects payments $\le 0$ with `HTTP 422 Unprocessable Entity`.
- **Cross-Tenant Access:** All queries strictly filter by `tenant_id`; cross-tenant requests return `HTTP 404 Not Found`.

## 5. How to Test
Run the test suite inside the API container:
```bash
docker compose exec api python -m unittest tests/test_projects.py -v
```

