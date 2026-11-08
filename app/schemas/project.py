import decimal
from datetime import date, datetime
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Project or engagement name")
    code: str = Field(..., min_length=2, max_length=100, description="Unique project reference code")
    description: Optional[str] = Field(None, max_length=1024)
    vendor_name: str = Field(..., min_length=2, max_length=255, description="Primary vendor or contractor")
    vendor_gstin: Optional[str] = Field(None, max_length=50, description="Vendor GSTIN / Tax ID")
    budget_amount: decimal.Decimal = Field(
        default=decimal.Decimal("0.00"),
        description="Agreed quotation / contract baseline amount (Gross)",
    )
    budget_currency: str = Field(default="INR", max_length=10)
    gst_rate_percent: decimal.Decimal = Field(
        default=decimal.Decimal("18.00"),
        description="Agreed or expected GST rate (e.g. 18.00 for 18%)",
    )
    over_billing_tolerance_percent: decimal.Decimal = Field(
        default=decimal.Decimal("5.00"),
        description="Allowed threshold before triggering over-budget alert",
    )
    single_invoice_cap: Optional[decimal.Decimal] = Field(
        default=None,
        description="Maximum permitted amount for any individual invoice",
    )
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    vendor_name: Optional[str] = Field(None, min_length=2, max_length=255)
    vendor_gstin: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    budget_amount: Optional[decimal.Decimal] = None
    budget_currency: Optional[str] = None
    gst_rate_percent: Optional[decimal.Decimal] = None
    over_billing_tolerance_percent: Optional[decimal.Decimal] = None
    single_invoice_cap: Optional[decimal.Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    vendor_name: str
    vendor_gstin: Optional[str] = None
    status: str
    budget_amount: decimal.Decimal
    budget_currency: str
    gst_rate_percent: decimal.Decimal
    over_billing_tolerance_percent: decimal.Decimal
    single_invoice_cap: Optional[decimal.Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectSummaryItem(ProjectResponse):
    total_invoiced_gross: decimal.Decimal = decimal.Decimal("0.00")
    total_invoiced_net: decimal.Decimal = decimal.Decimal("0.00")
    total_invoiced_gst: decimal.Decimal = decimal.Decimal("0.00")
    total_paid_gross: decimal.Decimal = decimal.Decimal("0.00")
    remaining_balance: decimal.Decimal = decimal.Decimal("0.00")
    variance_amount: decimal.Decimal = decimal.Decimal("0.00")
    variance_percent: decimal.Decimal = decimal.Decimal("0.00")
    burn_rate_percent: decimal.Decimal = decimal.Decimal("0.00")
    is_over_logged: bool = False
    documents_count: int = 0
    invoices_count: int = 0
    open_findings_count: int = 0


class ProjectListResponse(BaseModel):
    projects: list[ProjectSummaryItem]
    total: int


class InvoiceReconciliationItem(BaseModel):
    id: uuid.UUID
    invoice_number: str
    invoice_date: Optional[date] = None
    total_amount: decimal.Decimal
    tax_amount: decimal.Decimal
    net_amount: decimal.Decimal
    paid_amount: decimal.Decimal
    remaining_unpaid: decimal.Decimal
    payment_status: str
    po_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentReconciliationItem(BaseModel):
    id: uuid.UUID
    filename: str
    type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectReconciliationResponse(BaseModel):
    project: ProjectResponse

    # Quotation Baseline
    quoted_gross: decimal.Decimal
    quoted_net: decimal.Decimal
    quoted_gst: decimal.Decimal
    gst_rate_percent: decimal.Decimal

    # Invoiced Execution
    total_invoiced_gross: decimal.Decimal
    total_invoiced_net: decimal.Decimal
    total_invoiced_gst: decimal.Decimal
    invoice_count: int

    # Payment Tracking
    total_paid_gross: decimal.Decimal
    total_unpaid_gross: decimal.Decimal
    remaining_balance_under_quotation: decimal.Decimal
    uncommitted_budget: decimal.Decimal

    # Over / Under-Logged Burn Analysis
    variance_amount: decimal.Decimal
    variance_percent: decimal.Decimal
    burn_rate_percent: decimal.Decimal
    is_over_logged: bool
    over_logged_amount: decimal.Decimal
    under_logged_amount: decimal.Decimal
    tolerance_breached: bool

    # Line Item Invoices & Associated Docs
    invoices: list[InvoiceReconciliationItem]
    documents: list[DocumentReconciliationItem]
    findings_count: int
    open_findings_count: int


class PaymentRecordRequest(BaseModel):
    paid_amount: decimal.Decimal = Field(..., gt=0, description="Payment amount to record against this invoice")
    notes: Optional[str] = Field(None, max_length=500)

