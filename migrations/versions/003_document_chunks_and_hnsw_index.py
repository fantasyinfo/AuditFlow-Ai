"""document chunks and hnsw index

Revision ID: 003_document_chunks
Revises: 002_day2_tables
Create Date: 2026-11-06 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import pgvector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_document_chunks"
down_revision: Union[str, None] = "002_day2_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
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
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("ix_chunks_tenant_created", "document_chunks", ["tenant_id", "created_at"])
    op.create_index("ix_chunks_tenant_document", "document_chunks", ["tenant_id", "document_id"])

    # Create HNSW vector index
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw")
    op.drop_index("ix_chunks_tenant_document", table_name="document_chunks")
    op.drop_index("ix_chunks_tenant_created", table_name="document_chunks")
    op.drop_table("document_chunks")
