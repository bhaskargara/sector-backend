from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import regulatory_repository as repo
from app.schemas.regulatory import (
    AuditProcedureRead,
    ComplianceRequirementRead,
    EvidenceRead,
    LawRead,
    ObservationRead,
    ProvisionRead,
    SectorRead,
    SubSectorRead,
)

router = APIRouter()


@router.get("/sectors", response_model=list[SectorRead])
def get_sectors(sector_id: str | None = None, db: Session = Depends(get_db)):
    return repo.list_sectors(db, sector_id=sector_id)


@router.get("/sub-sectors", response_model=list[SubSectorRead])
def get_sub_sectors(
    sector_id: str | None = None,
    sub_sector_id: str | None = None,
    db: Session = Depends(get_db),
):
    return repo.list_sub_sectors(db, sector_id=sector_id, sub_sector_id=sub_sector_id)


@router.get("/laws", response_model=list[LawRead])
def get_laws(
    sector_id: str | None = None,
    sub_sector_id: str | None = None,
    law_id: str | None = None,
    compliance_area_id: str | None = None,
    db: Session = Depends(get_db),
):
    return repo.list_laws(
        db,
        sector_id=sector_id,
        sub_sector_id=sub_sector_id,
        law_id=law_id,
        compliance_area_id=compliance_area_id,
    )


@router.get("/provisions", response_model=list[ProvisionRead])
def get_provisions(
    sector_id: str | None = None,
    sub_sector_id: str | None = None,
    law_id: str | None = None,
    compliance_area_id: str | None = None,
    provision_id: str | None = None,
    origin: str | None = None,
    db: Session = Depends(get_db),
):
    return repo.list_provisions(
        db,
        sector_id=sector_id,
        sub_sector_id=sub_sector_id,
        law_id=law_id,
        compliance_area_id=compliance_area_id,
        provision_id=provision_id,
        origin=origin,
    )


@router.get("/compliance-requirements", response_model=list[ComplianceRequirementRead])
def get_compliance_requirements(
    compliance_id: str | None = None,
    provision_id: str | None = None,
    compliance_area_id: str | None = None,
    origin: str | None = None,
    db: Session = Depends(get_db),
):
    return repo.list_compliance_requirements(
        db,
        compliance_id=compliance_id,
        provision_id=provision_id,
        compliance_area_id=compliance_area_id,
        origin=origin,
    )


@router.get("/audit-procedures", response_model=list[AuditProcedureRead])
def get_audit_procedures(
    audit_id: str | None = None,
    compliance_id: str | None = None,
    origin: str | None = None,
    db: Session = Depends(get_db),
):
    return repo.list_audit_procedures(
        db,
        audit_id=audit_id,
        compliance_id=compliance_id,
        origin=origin,
    )


@router.get("/evidence", response_model=list[EvidenceRead])
def get_evidence(
    evidence_type: str | None = None,
    audit_id: str | None = None,
    origin: str | None = None,
    db: Session = Depends(get_db),
):
    return repo.list_evidence(
        db,
        evidence_type=evidence_type,
        audit_id=audit_id,
        origin=origin,
    )


@router.get("/observations", response_model=list[ObservationRead])
def get_observations(
    risk_level: str | None = None,
    audit_id: str | None = None,
    origin: str | None = None,
    db: Session = Depends(get_db),
):
    return repo.list_observations(
        db,
        risk_level=risk_level,
        audit_id=audit_id,
        origin=origin,
    )
