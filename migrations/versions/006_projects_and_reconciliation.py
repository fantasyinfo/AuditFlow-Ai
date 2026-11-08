"""projects table and reconciliation fields

Revision ID: 006_projects_reconciliation
Revises: 005_custom_rules
Create Date: 2026-11-07 15:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_projects_reconciliation"
down_revision: Union[str, None] = "005_custom_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create projects table
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("vendor_gstin", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("budget_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("budget_currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("gst_rate_percent", sa.Numeric(5, 2), nullable=False, server_default="18.00"),
        sa.Column("over_billing_tolerance_percent", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("single_invoice_cap", sa.Numeric(18, 2), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint(
        "uq_projects_tenant_code",
        "projects",
        ["tenant_id", "code"],
    )
    op.create_index("ix_projects_tenant_created", "projects", ["tenant_id", "created_at"])
    op.create_index("ix_projects_tenant_vendor", "projects", ["tenant_id", "vendor_name"])

    # 2. Add project_id to documents
    op.add_column("documents", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_documents_project_id",
        "documents",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_documents_tenant_project", "documents", ["tenant_id", "project_id"])

    # 3. Add project_id and financial dissection columns to invoices
    op.add_column("invoices", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("invoices", sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"))
    op.add_column("invoices", sa.Column("net_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"))
    op.add_column("invoices", sa.Column("paid_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"))
    op.add_column("invoices", sa.Column("payment_status", sa.String(length=50), nullable=False, server_default="unpaid"))
    op.create_foreign_key(
        "fk_invoices_project_id",
        "invoices",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_invoices_tenant_project", "invoices", ["tenant_id", "project_id"])

    # 4. Add project_id to findings
    op.add_column("findings", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_findings_project_id",
        "findings",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_findings_tenant_project", "findings", ["tenant_id", "project_id"])

    # 5. Add project_id to custom_rules
    op.add_column("custom_rules", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_custom_rules_project_id",
        "custom_rules",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_custom_rules_tenant_project", "custom_rules", ["tenant_id", "project_id"])


def downgrade() -> None:
    op.drop_index("ix_custom_rules_tenant_project", table_name="custom_rules")
    op.drop_constraint("fk_custom_rules_project_id", "custom_rules", type_="foreignkey")
    op.drop_column("custom_rules", "project_id")

    op.drop_index("ix_findings_tenant_project", table_name="findings")
    op.drop_constraint("fk_findings_project_id", "findings", type_="foreignkey")
    op.drop_column("findings", "project_id")

    op.drop_index("ix_invoices_tenant_project", table_name="invoices")
    op.drop_constraint("fk_invoices_project_id", "invoices", type_="foreignkey")
    op.drop_column("invoices", "payment_status")
    op.drop_column("invoices", "paid_amount")
    op.drop_column("invoices", "net_amount")
    op.drop_column("invoices", "tax_amount")
    op.drop_column("invoices", "project_id")

    op.drop_index("ix_documents_tenant_project", table_name="documents")
    op.drop_constraint("fk_documents_project_id", "documents", type_="foreignkey")
    op.drop_column("documents", "project_id")

    op.drop_index("ix_projects_tenant_vendor", table_name="projects")
    op.drop_index("ix_projects_tenant_created", table_name="projects")
    op.drop_constraint("uq_projects_tenant_code", "projects", type_="unique")
    op.drop_table("projects")

