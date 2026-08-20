from datetime import date

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.organization import ClientMaster, FirmEnterpriseEngagement, FirmMaster


class AuditEngagement(TimestampMixin, Base):
    __tablename__ = "audit_engagement"

    audit_id: Mapped[str] = mapped_column(primary_key=True)
    firm_id: Mapped[str] = mapped_column(
        ForeignKey("firm_master.firm_id"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[str] = mapped_column(
        ForeignKey("client_master.client_id"),
        nullable=False,
        index=True,
    )
    engagement_id: Mapped[str | None] = mapped_column(
        ForeignKey("firm_enterprise_engagement.engagement_id"),
        index=True,
    )
    audit_type: Mapped[str] = mapped_column(nullable=False, index=True)
    audit_period_label: Mapped[str] = mapped_column(nullable=False, index=True)
    period_start: Mapped[date | None]
    period_end: Mapped[date | None]
    status: Mapped[str] = mapped_column(default="Draft", nullable=False, index=True)
    sector_id: Mapped[str] = mapped_column(nullable=False, index=True)
    sub_sector_id: Mapped[str] = mapped_column(nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(nullable=False, index=True)
    sector_name: Mapped[str | None]
    sub_sector_name: Mapped[str | None]
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text)

    firm: Mapped[FirmMaster] = relationship()
    client: Mapped[ClientMaster] = relationship()
    engagement_ref: Mapped[FirmEnterpriseEngagement | None] = relationship()


class AuditEngagementItem(TimestampMixin, Base):
    __tablename__ = "audit_engagement_item"

    item_id: Mapped[str] = mapped_column(primary_key=True)
    audit_id: Mapped[str] = mapped_column(
        ForeignKey("audit_engagement.audit_id"),
        nullable=False,
        index=True,
    )
    law_id: Mapped[str | None] = mapped_column(index=True)
    law_name: Mapped[str | None] = mapped_column(index=True)
    regulator: Mapped[str | None] = mapped_column(index=True)
    authority_level: Mapped[str | None] = mapped_column(index=True)
    document_type: Mapped[str | None] = mapped_column(index=True)
    applicability_type: Mapped[str | None] = mapped_column(index=True)
    applicability_trigger: Mapped[str | None] = mapped_column(Text)
    provision_id: Mapped[str | None] = mapped_column(index=True)
    provision_name: Mapped[str | None]
    statutory_reference: Mapped[str | None] = mapped_column(index=True)
    compliance_id: Mapped[str | None] = mapped_column(index=True)
    compliance_requirement: Mapped[str | None] = mapped_column(Text)
    compliance_objective: Mapped[str | None] = mapped_column(Text)
    compliance_frequency: Mapped[str | None] = mapped_column(index=True)
    audit_procedure_id: Mapped[str | None] = mapped_column(index=True)
    audit_procedure: Mapped[str | None] = mapped_column(Text)
    audit_method: Mapped[str | None]
    audit_frequency: Mapped[str | None] = mapped_column(index=True)
    evidence_template: Mapped[str | None] = mapped_column(Text)
    evidence_type: Mapped[str | None] = mapped_column(index=True)
    evidence_mandatory: Mapped[str | None] = mapped_column(index=True)
    observation_template: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(index=True)
    risk_level: Mapped[str | None] = mapped_column(index=True)
    origin: Mapped[str | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(default="Pending", nullable=False, index=True)
    auditor_remarks: Mapped[str | None] = mapped_column(Text)
    observation_notes: Mapped[str | None] = mapped_column(Text)
    evidence_notes: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    engagement: Mapped[AuditEngagement] = relationship()


class AuditEvidenceAttachment(TimestampMixin, Base):
    __tablename__ = "audit_evidence_attachment"

    attachment_id: Mapped[str] = mapped_column(primary_key=True)
    item_id: Mapped[str] = mapped_column(
        ForeignKey("audit_engagement_item.item_id"),
        nullable=False,
        index=True,
    )
    original_file_name: Mapped[str] = mapped_column(nullable=False)
    stored_file_name: Mapped[str] = mapped_column(nullable=False)
    content_type: Mapped[str | None]
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relative_path: Mapped[str] = mapped_column(nullable=False)

    item: Mapped[AuditEngagementItem] = relationship()
