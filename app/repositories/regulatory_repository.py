from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.regulatory import (
    AuditProcedureMaster,
    ComplianceRequirementMaster,
    EvidenceMaster,
    LawComplianceAreaMap,
    LawMaster,
    ObservationMaster,
    ProvisionComplianceAreaMap,
    ProvisionMaster,
    SectorMaster,
    SubSectorMaster,
)


def list_sectors(db: Session, sector_id: str | None = None):
    stmt = select(SectorMaster).order_by(SectorMaster.sector_name)
    if sector_id:
        stmt = stmt.where(SectorMaster.sector_id == sector_id)
    return db.scalars(stmt).all()


def list_sub_sectors(db: Session, sector_id: str | None = None, sub_sector_id: str | None = None):
    stmt = select(SubSectorMaster).order_by(SubSectorMaster.sub_sector_name)
    if sector_id:
        stmt = stmt.where(SubSectorMaster.sector_id == sector_id)
    if sub_sector_id:
        stmt = stmt.where(SubSectorMaster.sub_sector_id == sub_sector_id)
    return db.scalars(stmt).all()


def list_laws(db: Session, sector_id: str | None = None, sub_sector_id: str | None = None, law_id: str | None = None, compliance_area_id: str | None = None):
    stmt = select(LawMaster).distinct().order_by(LawMaster.law_name)
    if law_id:
        stmt = stmt.where(LawMaster.law_id == law_id)
    if sector_id:
        stmt = stmt.join(SectorMaster, SectorMaster.sector_name == LawMaster.sector).where(SectorMaster.sector_id == sector_id)
    if sub_sector_id:
        stmt = stmt.join(SubSectorMaster, SubSectorMaster.sub_sector_name == LawMaster.sub_sector).where(SubSectorMaster.sub_sector_id == sub_sector_id)
    if compliance_area_id:
        stmt = stmt.join(LawComplianceAreaMap, LawComplianceAreaMap.law_id == LawMaster.law_id).where(LawComplianceAreaMap.compliance_area_id == compliance_area_id)
    return db.scalars(stmt).all()


def list_provisions(db: Session, sector_id: str | None = None, sub_sector_id: str | None = None, law_id: str | None = None, compliance_area_id: str | None = None, provision_id: str | None = None, origin: str | None = None):
    stmt = select(ProvisionMaster).distinct().order_by(ProvisionMaster.provision_id)
    if provision_id:
        stmt = stmt.where(ProvisionMaster.provision_id == provision_id)
    if law_id:
        stmt = stmt.where(ProvisionMaster.law_id == law_id)
    if sub_sector_id:
        stmt = stmt.where(ProvisionMaster.sub_sector_id == sub_sector_id)
    if origin:
        stmt = stmt.where(ProvisionMaster.origin == origin)
    if sector_id:
        stmt = stmt.join(SubSectorMaster, SubSectorMaster.sub_sector_id == ProvisionMaster.sub_sector_id).where(SubSectorMaster.sector_id == sector_id)
    if compliance_area_id:
        stmt = stmt.join(ProvisionComplianceAreaMap, ProvisionComplianceAreaMap.provision_id == ProvisionMaster.provision_id).where(ProvisionComplianceAreaMap.compliance_area_id == compliance_area_id)
    return db.scalars(stmt).all()


def list_compliance_requirements(db: Session, compliance_id: str | None = None, provision_id: str | None = None, compliance_area_id: str | None = None, origin: str | None = None):
    stmt = select(ComplianceRequirementMaster).order_by(ComplianceRequirementMaster.compliance_id)
    if compliance_id:
        stmt = stmt.where(ComplianceRequirementMaster.compliance_id == compliance_id)
    if provision_id:
        stmt = stmt.where(ComplianceRequirementMaster.provision_id == provision_id)
    if compliance_area_id:
        stmt = stmt.where(ComplianceRequirementMaster.compliance_area_id == compliance_area_id)
    if origin:
        stmt = stmt.where(ComplianceRequirementMaster.origin == origin)
    return db.scalars(stmt).all()


def list_audit_procedures(db: Session, audit_id: str | None = None, compliance_id: str | None = None, origin: str | None = None):
    stmt = select(AuditProcedureMaster).order_by(AuditProcedureMaster.audit_id)
    if audit_id:
        stmt = stmt.where(AuditProcedureMaster.audit_id == audit_id)
    if compliance_id:
        stmt = stmt.where(AuditProcedureMaster.compliance_id == compliance_id)
    if origin:
        stmt = stmt.where(AuditProcedureMaster.origin == origin)
    return db.scalars(stmt).all()


def list_evidence(db: Session, evidence_type: str | None = None, audit_id: str | None = None, origin: str | None = None):
    stmt = select(EvidenceMaster).order_by(EvidenceMaster.evidence_id)
    if evidence_type:
        stmt = stmt.where(EvidenceMaster.evidence_type == evidence_type)
    if audit_id:
        stmt = stmt.where(EvidenceMaster.audit_id == audit_id)
    if origin:
        stmt = stmt.where(EvidenceMaster.origin == origin)
    return db.scalars(stmt).all()


def list_observations(db: Session, risk_level: str | None = None, audit_id: str | None = None, origin: str | None = None):
    stmt = select(ObservationMaster).order_by(ObservationMaster.observation_id)
    if risk_level:
        stmt = stmt.where(ObservationMaster.risk_level == risk_level)
    if audit_id:
        stmt = stmt.where(ObservationMaster.audit_id == audit_id)
    if origin:
        stmt = stmt.where(ObservationMaster.origin == origin)
    return db.scalars(stmt).all()
