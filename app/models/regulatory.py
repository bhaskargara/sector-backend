from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class SectorMaster(TimestampMixin, Base):
    __tablename__ = "sector_master"

    sector_id: Mapped[str] = mapped_column(primary_key=True)
    sector_name: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[str] = mapped_column(nullable=False, index=True)
    remark: Mapped[str | None] = mapped_column(Text)


class SubSectorMaster(TimestampMixin, Base):
    __tablename__ = "sub_sector_master"

    sub_sector_id: Mapped[str] = mapped_column(primary_key=True)
    sector_id: Mapped[str] = mapped_column(
        ForeignKey("sector_master.sector_id"),
        nullable=False,
        index=True,
    )
    sub_sector_name: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[str] = mapped_column(nullable=False, index=True)

    sector: Mapped[SectorMaster] = relationship()


class RegulatoryAuthorityMaster(TimestampMixin, Base):
    __tablename__ = "regulatory_authority_master"

    authority_id: Mapped[str] = mapped_column(primary_key=True)
    regulatory_authority: Mapped[str] = mapped_column(nullable=False, index=True)
    short_name: Mapped[str | None] = mapped_column(index=True)
    authority_type: Mapped[str | None] = mapped_column(index=True)
    jurisdiction: Mapped[str | None] = mapped_column(index=True)
    parent_authority: Mapped[str | None]
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[str] = mapped_column(nullable=False, index=True)


class ComplianceAreaMaster(TimestampMixin, Base):
    __tablename__ = "compliance_area_master"

    area_id: Mapped[str] = mapped_column(primary_key=True)
    parent_area_id: Mapped[str | None] = mapped_column(
        ForeignKey("compliance_area_master.area_id"),
        index=True,
    )
    parent_area: Mapped[str | None] = mapped_column(index=True)
    compliance_area: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int | None]
    active: Mapped[str] = mapped_column(nullable=False, index=True)

    parent: Mapped["ComplianceAreaMaster | None"] = relationship(
        remote_side=[area_id]
    )


class OriginMaster(TimestampMixin, Base):
    __tablename__ = "origin_master"

    origin_code: Mapped[str] = mapped_column(primary_key=True)
    origin_name: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)


class EnumMaster(TimestampMixin, Base):
    __tablename__ = "enum_master"
    __table_args__ = (
        PrimaryKeyConstraint("enum_type", "allowed_value", name="pk_enum_master"),
    )

    enum_type: Mapped[str] = mapped_column(index=True)
    allowed_value: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column(Text)


class LawMaster(TimestampMixin, Base):
    __tablename__ = "law_master"

    law_id: Mapped[str] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(nullable=False, index=True)
    sector: Mapped[str] = mapped_column(nullable=False, index=True)
    sub_sector: Mapped[str] = mapped_column(nullable=False, index=True)
    regulator: Mapped[str] = mapped_column(nullable=False, index=True)
    authority_level: Mapped[str | None] = mapped_column(index=True)
    document_type: Mapped[str] = mapped_column(nullable=False, index=True)
    parent_law: Mapped[str | None] = mapped_column(
        ForeignKey("law_master.law_id"),
        index=True,
    )
    law_name: Mapped[str] = mapped_column(nullable=False, index=True)
    law_compliance_area_map: Mapped[str | None]
    applicability_type: Mapped[str] = mapped_column(nullable=False, index=True)
    applicability_trigger: Mapped[str | None] = mapped_column(Text)
    active: Mapped[str] = mapped_column(nullable=False, index=True)
    review_frequency: Mapped[str | None] = mapped_column(index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    parent: Mapped["LawMaster | None"] = relationship(remote_side=[law_id])


class LawComplianceAreaMap(TimestampMixin, Base):
    __tablename__ = "law_compliance_area_map"

    map_id: Mapped[str] = mapped_column(primary_key=True)
    law_id: Mapped[str] = mapped_column(
        ForeignKey("law_master.law_id"),
        nullable=False,
        index=True,
    )
    compliance_area_id: Mapped[str] = mapped_column(
        ForeignKey("compliance_area_master.area_id"),
        nullable=False,
        index=True,
    )
    active_status: Mapped[str] = mapped_column(nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    law: Mapped[LawMaster] = relationship()
    compliance_area: Mapped[ComplianceAreaMaster] = relationship()


class ProvisionMaster(TimestampMixin, Base):
    __tablename__ = "provision_master"

    provision_id: Mapped[str] = mapped_column(primary_key=True)
    law_id: Mapped[str] = mapped_column(
        ForeignKey("law_master.law_id"),
        nullable=False,
        index=True,
    )
    sub_sector_id: Mapped[str | None] = mapped_column(
        ForeignKey("sub_sector_master.sub_sector_id"),
        index=True,
    )
    provision_category: Mapped[str] = mapped_column(nullable=False, index=True)
    statutory_reference: Mapped[str | None] = mapped_column(index=True)
    provision_name: Mapped[str] = mapped_column(nullable=False, index=True)
    provision_description: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(
        ForeignKey("origin_master.origin_code"),
        nullable=False,
        index=True,
    )
    active: Mapped[str] = mapped_column(nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    law: Mapped[LawMaster] = relationship()
    sub_sector_ref: Mapped[SubSectorMaster | None] = relationship()
    origin_ref: Mapped[OriginMaster] = relationship()


class ProvisionComplianceAreaMap(TimestampMixin, Base):
    __tablename__ = "provision_compliance_area_map"

    map_id: Mapped[str] = mapped_column(primary_key=True)
    provision_id: Mapped[str] = mapped_column(
        ForeignKey("provision_master.provision_id"),
        nullable=False,
        index=True,
    )
    compliance_area_id: Mapped[str] = mapped_column(
        ForeignKey("compliance_area_master.area_id"),
        nullable=False,
        index=True,
    )
    active: Mapped[str] = mapped_column(nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    provision: Mapped[ProvisionMaster] = relationship()
    compliance_area: Mapped[ComplianceAreaMaster] = relationship()


class ComplianceRequirementMaster(TimestampMixin, Base):
    __tablename__ = "compliance_requirement_master"

    compliance_id: Mapped[str] = mapped_column(primary_key=True)
    provision_id: Mapped[str] = mapped_column(
        ForeignKey("provision_master.provision_id"),
        nullable=False,
        index=True,
    )
    compliance_area_id: Mapped[str] = mapped_column(
        ForeignKey("compliance_area_master.area_id"),
        nullable=False,
        index=True,
    )
    compliance_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    compliance_objective: Mapped[str | None] = mapped_column(Text)
    applicability: Mapped[str | None] = mapped_column(index=True)
    frequency: Mapped[str | None] = mapped_column(index=True)
    due_timeline: Mapped[str | None]
    responsible_person: Mapped[str | None] = mapped_column(index=True)
    non_compliance_consequence: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(index=True)
    origin: Mapped[str] = mapped_column(
        ForeignKey("origin_master.origin_code"),
        nullable=False,
        index=True,
    )
    active: Mapped[str] = mapped_column(nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    provision: Mapped[ProvisionMaster] = relationship()
    compliance_area: Mapped[ComplianceAreaMaster] = relationship()
    origin_ref: Mapped[OriginMaster] = relationship()


class AuditProcedureMaster(TimestampMixin, Base):
    __tablename__ = "audit_procedure_master"

    audit_id: Mapped[str] = mapped_column(primary_key=True)
    compliance_id: Mapped[str] = mapped_column(
        ForeignKey("compliance_requirement_master.compliance_id"),
        nullable=False,
        index=True,
    )
    audit_procedure: Mapped[str] = mapped_column(Text, nullable=False)
    audit_method: Mapped[str | None] = mapped_column(index=True)
    audit_frequency: Mapped[str | None] = mapped_column(index=True)
    origin: Mapped[str] = mapped_column(
        ForeignKey("origin_master.origin_code"),
        nullable=False,
        index=True,
    )
    risk_focus: Mapped[str | None] = mapped_column(Text)
    active: Mapped[str] = mapped_column(nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    compliance: Mapped[ComplianceRequirementMaster] = relationship()
    origin_ref: Mapped[OriginMaster] = relationship()


class EvidenceMaster(TimestampMixin, Base):
    __tablename__ = "evidence_master"

    evidence_id: Mapped[str] = mapped_column(primary_key=True)
    audit_id: Mapped[str] = mapped_column(
        ForeignKey("audit_procedure_master.audit_id"),
        nullable=False,
        index=True,
    )
    evidence_required: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str | None] = mapped_column(index=True)
    mandatory: Mapped[str] = mapped_column(nullable=False, index=True)
    retention_category: Mapped[str | None] = mapped_column(index=True)
    origin: Mapped[str] = mapped_column(
        ForeignKey("origin_master.origin_code"),
        nullable=False,
        index=True,
    )
    active: Mapped[str] = mapped_column(nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    audit: Mapped[AuditProcedureMaster] = relationship()
    origin_ref: Mapped[OriginMaster] = relationship()


class ObservationMaster(TimestampMixin, Base):
    __tablename__ = "observation_master"

    observation_id: Mapped[str] = mapped_column(primary_key=True)
    audit_id: Mapped[str] = mapped_column(
        ForeignKey("audit_procedure_master.audit_id"),
        nullable=False,
        index=True,
    )
    observation_template: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(nullable=False, index=True)
    recommendation: Mapped[str | None] = mapped_column(Text)
    observation_category: Mapped[str | None] = mapped_column(index=True)
    origin: Mapped[str] = mapped_column(
        ForeignKey("origin_master.origin_code"),
        nullable=False,
        index=True,
    )
    active: Mapped[str] = mapped_column(nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    audit: Mapped[AuditProcedureMaster] = relationship()
    origin_ref: Mapped[OriginMaster] = relationship()


class ImportLog(TimestampMixin, Base):
    __tablename__ = "import_log"

    import_log_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workbook_path: Mapped[str] = mapped_column(nullable=False)
    mode: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)


Index("ix_law_sector_sub_sector", LawMaster.sector, LawMaster.sub_sector)
Index(
    "ix_compliance_provision_area",
    ComplianceRequirementMaster.provision_id,
    ComplianceRequirementMaster.compliance_area_id,
)
Index("ix_evidence_audit_type", EvidenceMaster.audit_id, EvidenceMaster.evidence_type)
Index(
    "ix_observation_audit_risk",
    ObservationMaster.audit_id,
    ObservationMaster.risk_level,
)
