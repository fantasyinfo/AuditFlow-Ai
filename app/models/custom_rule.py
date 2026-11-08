import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CustomRule(Base):
    __tablename__ = "custom_rules"

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
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    field_to_evaluate: Mapped[str] = mapped_column(String(50), default="total_amount", nullable=False)
    operator: Mapped[str] = mapped_column(String(20), default=">", nullable=False)
    threshold_value: Mapped[str] = mapped_column(String(255), nullable=False)
    reason_template: Mapped[str] = mapped_column(
        String(1024),
        default="Invoice violates custom policy rule {name}.",
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    project: Mapped["Project | None"] = relationship("Project", back_populates="custom_rules")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_custom_rules_tenant_code"),
        Index("ix_custom_rules_tenant_created", "tenant_id", "created_at"),
        Index("ix_custom_rules_tenant_active", "tenant_id", "is_active"),
        Index("ix_custom_rules_tenant_project", "tenant_id", "project_id"),
    )

