"""documents invoices purchase_orders and idempotency_keys

Revision ID: 002_day2_tables
Revises: 001_initial
Create Date: 2026-11-06 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_day2_tables"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False, server_default="invoice"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_tenant_created", "documents", ["tenant_id", "created_at"])
    op.create_index("ix_documents_tenant_status", "documents", ["tenant_id", "status"])

    # 2. purchase_orders table
    op.create_table(
        "purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("po_number", sa.String(length=100), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "po_number", name="uq_pos_tenant_po_number"),
    )
    op.create_index("ix_pos_tenant_created", "purchase_orders", ["tenant_id", "created_at"])

    # 3. invoices table
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("vendor_gstin", sa.String(length=50), nullable=True),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "po_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("purchase_orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "vendor_name", "invoice_number", name="uq_invoices_tenant_vendor_number"),
    )
    op.create_index("ix_invoices_tenant_created", "invoices", ["tenant_id", "created_at"])
    op.create_index("ix_invoices_document_id", "invoices", ["document_id"])
    op.create_index("ix_invoices_po_id", "invoices", ["po_id"])

    # 4. idempotency_keys table
    op.create_table(
        "idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("response_hash", sa.String(length=64), nullable=True),
        sa.Column("response_code", sa.Integer(), nullable=False, server_default="202"),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "key", name="uq_idempotency_tenant_key"),
    )
    op.create_index("ix_idempotency_tenant_created", "idempotency_keys", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_table("invoices")
    op.drop_table("purchase_orders")
    op.drop_table("documents")
