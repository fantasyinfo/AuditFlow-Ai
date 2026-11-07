"""custom_rules table

Revision ID: 005_custom_rules
Revises: 004_findings_audit
Create Date: 2026-11-07 08:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_custom_rules"
down_revision: Union[str, None] = "004_findings_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "custom_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="medium"),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("field_to_evaluate", sa.String(length=50), nullable=False, server_default="total_amount"),
        sa.Column("operator", sa.String(length=20), nullable=False, server_default=">"),
        sa.Column("threshold_value", sa.String(length=255), nullable=False),
        sa.Column("reason_template", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint(
        "uq_custom_rules_tenant_code",
        "custom_rules",
        ["tenant_id", "code"],
    )
    op.create_index("ix_custom_rules_tenant_created", "custom_rules", ["tenant_id", "created_at"])
    op.create_index("ix_custom_rules_tenant_active", "custom_rules", ["tenant_id", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_custom_rules_tenant_active", table_name="custom_rules")
    op.drop_index("ix_custom_rules_tenant_created", table_name="custom_rules")
    op.drop_constraint("uq_custom_rules_tenant_code", "custom_rules", type_="unique")
    op.drop_table("custom_rules")

