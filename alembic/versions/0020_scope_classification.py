"""Keep broad sector laws out of sub-sector audit buckets.

Revision ID: 0020_scope_classification
Revises: 0019_multi_sub_sector_audits
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0020_scope_classification"
down_revision: str | None = "0019_multi_sub_sector_audits"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # A Law Master scope of "All" applies across its sector. Earlier runtime
    # composition allowed Applicability Matrix matches to override that broad
    # scope, so correct the snapshots while retaining every audit response.
    for schema_name in ("pharmacy", "bank", "it", "manufacturing", "nbfc"):
        op.execute(
            sa.text(
                f"""
                UPDATE audit_engagement_item AS item
                SET applicability_scope = 'SECTOR_WIDE'
                FROM audit_engagement AS engagement,
                     {schema_name}.law_master AS law
                WHERE item.audit_id = engagement.audit_id
                  AND law.law_id = item.law_id
                  AND item.dataset_key = '{schema_name}'
                  AND item.source_scope = 'SECTOR'
                  AND lower(trim(law.sub_sector)) = 'all'
                  AND NOT EXISTS (
                    SELECT 1
                    FROM {schema_name}.provision_master AS provision
                    WHERE provision.provision_id = item.provision_id
                      AND provision.sub_sector_id IN (
                        SELECT jsonb_array_elements_text(engagement.sub_sector_ids)
                      )
                  )
                """
            )
        )


def downgrade() -> None:
    # Scope labels are a data correction and cannot be safely inferred back.
    pass
