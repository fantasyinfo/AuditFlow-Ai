import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FindingStatus(str, enum.Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


class FindingSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding(Base):
    __tablename__ = "findings"

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
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rule: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default=FindingSeverity.MEDIUM.value, nullable=False)
    reason: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=FindingStatus.OPEN.value, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    invoice: Mapped["Invoice"] = relationship("Invoice")
    project: Mapped["Project | None"] = relationship("Project", back_populates="findings")

    __table_args__ = (
        Index("ix_findings_tenant_created", "tenant_id", "created_at"),
        Index("ix_findings_tenant_status", "tenant_id", "status"),
        Index("ix_findings_tenant_rule", "tenant_id", "rule"),
        Index("ix_findings_tenant_project", "tenant_id", "project_id"),
    )
