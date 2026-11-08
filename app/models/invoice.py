import decimal
import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

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
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_gstin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(18, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    net_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(18, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    paid_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(18, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    payment_status: Mapped[str] = mapped_column(String(50), default="unpaid", nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    document: Mapped["Document"] = relationship("Document")
    purchase_order: Mapped["PurchaseOrder | None"] = relationship("PurchaseOrder")
    project: Mapped["Project | None"] = relationship("Project", back_populates="invoices")

    __table_args__ = (
        Index("ix_invoices_tenant_created", "tenant_id", "created_at"),
        Index("ix_invoices_tenant_project", "tenant_id", "project_id"),
        UniqueConstraint("tenant_id", "vendor_name", "invoice_number", name="uq_invoices_tenant_vendor_number"),
    )
