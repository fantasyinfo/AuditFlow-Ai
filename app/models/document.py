import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"
    QUOTATION = "quotation"
    AGREEMENT = "agreement"
    CONTRACT = "contract"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default=DocumentType.INVOICE.value, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=DocumentStatus.QUEUED.value, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    uploader: Mapped["User"] = relationship("User")
    project: Mapped["Project | None"] = relationship("Project", back_populates="documents")

    __table_args__ = (
        Index("ix_documents_tenant_created", "tenant_id", "created_at"),
        Index("ix_documents_tenant_status", "tenant_id", "status"),
        Index("ix_documents_tenant_project", "tenant_id", "project_id"),
    )
