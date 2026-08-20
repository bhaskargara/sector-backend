from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.audit import AuditEngagement, AuditEngagementItem
from app.models.organization import ClientMaster, FirmMaster
from app.models.regulatory import SectorMaster, SubSectorMaster
from app.models.regulatory import (
    AuditProcedureMaster,
    ComplianceAreaMaster,
    ComplianceRequirementMaster,
    LawMaster,
    OriginMaster,
    ProvisionMaster,
)
from app.repositories.audit_repository import create_audit
from app.schemas.audit import AuditEngagementCreate


def test_sector_and_sub_sector_model_fk():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(SectorMaster(sector_id="SEC001", sector_name="Pharmacy", active="Yes"))
        db.add(
            SubSectorMaster(
                sub_sector_id="SUB001",
                sector_id="SEC001",
                sub_sector_name="Retail Pharmacy",
                active="Yes",
            )
        )
        db.commit()
        assert db.get(SubSectorMaster, "SUB001").sector_id == "SEC001"


def test_create_audit_generates_snapshot_items():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(OriginMaster(origin_code="CORE", origin_name="Core"))
        db.add(
            ComplianceAreaMaster(
                area_id="AREA001",
                compliance_area="Board Governance",
                active="Yes",
            )
        )
        db.add(SectorMaster(sector_id="SEC001", sector_name="Pharmacy", active="Yes"))
        db.add(
            SubSectorMaster(
                sub_sector_id="SUB001",
                sector_id="SEC001",
                sub_sector_name="Retail Pharmacy",
                active="Yes",
            )
        )
        db.add(
            FirmMaster(
                firm_id="FIRM-PCS",
                firm_name="PCS",
                status="Active",
            )
        )
        db.add(
            ClientMaster(
                client_id="CLT-001",
                firm_id="FIRM-PCS",
                client_name="Apollo Retail Pharmacy",
                sector_id="SEC001",
                sub_sector_id="SUB001",
                status="Active",
            )
        )
        db.add(
            LawMaster(
                law_id="LAW001",
                domain="Secretarial",
                sector="Pharmacy",
                sub_sector="Retail Pharmacy",
                regulator="MCA",
                document_type="Act",
                law_name="Companies Act",
                applicability_type="Mandatory",
                active="Yes",
            )
        )
        db.add(
            ProvisionMaster(
                provision_id="PRV001",
                law_id="LAW001",
                sub_sector_id="SUB001",
                provision_category="Board",
                provision_name="Board Meeting Compliance",
                origin="CORE",
                active="Yes",
            )
        )
        db.add(
            ComplianceRequirementMaster(
                compliance_id="CMP001",
                provision_id="PRV001",
                compliance_area_id="AREA001",
                compliance_requirement="Hold required board meetings",
                origin="CORE",
                active="Yes",
            )
        )
        db.add(
            AuditProcedureMaster(
                audit_id="AUDPROC001",
                compliance_id="CMP001",
                audit_procedure="Review minutes and board calendar",
                origin="CORE",
                active="Yes",
            )
        )
        db.commit()

        engagement = create_audit(
            db,
            "FIRM-PCS",
            AuditEngagementCreate(
                client_id="CLT-001",
                audit_period_label="FY 2025-26",
            ),
        )

        assert db.get(AuditEngagement, engagement.audit_id) is not None
        items = db.query(AuditEngagementItem).filter_by(audit_id=engagement.audit_id).all()
        assert len(items) == 1
        assert items[0].law_name == "Companies Act"
        assert items[0].status == "Pending"
