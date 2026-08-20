"""create pharmacy regulatory master tables

Revision ID: 0001_pharmacy_regulatory
Revises:
Create Date: 2026-07-08
"""
from collections.abc import Sequence

from app.core.database import Base
from app.models.regulatory import (
    AuditProcedureMaster,
    ComplianceAreaMaster,
    ComplianceRequirementMaster,
    EnumMaster,
    EvidenceMaster,
    ImportLog,
    LawComplianceAreaMap,
    LawMaster,
    ObservationMaster,
    OriginMaster,
    ProvisionComplianceAreaMap,
    ProvisionMaster,
    RegulatoryAuthorityMaster,
    SectorMaster,
    SubSectorMaster,
)
from alembic import op

revision: str = "0001_pharmacy_regulatory"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(
        bind,
        tables=[
            SectorMaster.__table__,
            SubSectorMaster.__table__,
            RegulatoryAuthorityMaster.__table__,
            ComplianceAreaMaster.__table__,
            OriginMaster.__table__,
            EnumMaster.__table__,
            LawMaster.__table__,
            LawComplianceAreaMap.__table__,
            ProvisionMaster.__table__,
            ProvisionComplianceAreaMap.__table__,
            ComplianceRequirementMaster.__table__,
            AuditProcedureMaster.__table__,
            EvidenceMaster.__table__,
            ObservationMaster.__table__,
            ImportLog.__table__,
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(
        bind,
        tables=[
            ImportLog.__table__,
            ObservationMaster.__table__,
            EvidenceMaster.__table__,
            AuditProcedureMaster.__table__,
            ComplianceRequirementMaster.__table__,
            ProvisionComplianceAreaMap.__table__,
            ProvisionMaster.__table__,
            LawComplianceAreaMap.__table__,
            LawMaster.__table__,
            EnumMaster.__table__,
            OriginMaster.__table__,
            ComplianceAreaMaster.__table__,
            RegulatoryAuthorityMaster.__table__,
            SubSectorMaster.__table__,
            SectorMaster.__table__,
        ],
    )
