import decimal
import enum
import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    FLAGGED = "flagged"


class Project(Base):
    __tablename__ = "projects"

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_gstin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=ProjectStatus.ACTIVE.value, nullable=False)

    # Quotation and Budget Baselines
    budget_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(18, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    budget_currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    gst_rate_percent: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 2),
        default=decimal.Decimal("18.00"),
        nullable=False,
    )
    over_billing_tolerance_percent: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 2),
        default=decimal.Decimal("5.00"),
        nullable=False,
    )
    single_invoice_cap: Mapped[decimal.Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="project")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="project")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="project")
    custom_rules: Mapped[list["CustomRule"]] = relationship("CustomRule", back_populates="project")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_projects_tenant_code"),
        Index("ix_projects_tenant_created", "tenant_id", "created_at"),
        Index("ix_projects_tenant_vendor", "tenant_id", "vendor_name"),
    )

