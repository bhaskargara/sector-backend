"""Record the real applicability level on every audit item snapshot.

Revision ID: 0014_item_scope
Revises: 0012_clean_slate_legacy
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0014_item_scope"
down_revision: str | None = "0012_clean_slate_legacy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audit_engagement_item",
        sa.Column("applicability_scope", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_audit_engagement_item_applicability_scope",
        "audit_engagement_item",
        ["applicability_scope"],
    )

    # Existing audit snapshots did not retain the provision's sub-sector ID.
    # Resolve it once from the same dataset that created each audit item.
    op.execute("""
        UPDATE audit_engagement_item item
        SET applicability_scope = CASE
            WHEN item.dataset_key = 'common_core' THEN 'COMMON_CORE'
            WHEN item.dataset_key = 'pharmacy' AND EXISTS (
                SELECT 1 FROM pharmacy.provision_master provision
                JOIN audit_engagement audit ON audit.audit_id = item.audit_id
                WHERE provision.provision_id = item.provision_id
                  AND provision.sub_sector_id = audit.sub_sector_id
            ) THEN 'SUB_SECTOR'
            WHEN item.dataset_key = 'bank' AND EXISTS (
                SELECT 1 FROM bank.provision_master provision
                JOIN audit_engagement audit ON audit.audit_id = item.audit_id
                WHERE provision.provision_id = item.provision_id
                  AND provision.sub_sector_id = audit.sub_sector_id
            ) THEN 'SUB_SECTOR'
            WHEN item.dataset_key = 'it' AND EXISTS (
                SELECT 1 FROM it.provision_master provision
                JOIN audit_engagement audit ON audit.audit_id = item.audit_id
                WHERE provision.provision_id = item.provision_id
                  AND provision.sub_sector_id = audit.sub_sector_id
            ) THEN 'SUB_SECTOR'
            ELSE 'SECTOR_WIDE'
        END
    """)
    op.alter_column("audit_engagement_item", "applicability_scope", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_audit_engagement_item_applicability_scope", table_name="audit_engagement_item")
    op.drop_column("audit_engagement_item", "applicability_scope")
