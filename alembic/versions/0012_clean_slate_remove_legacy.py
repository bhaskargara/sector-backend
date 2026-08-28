"""Purge audit records and drop the retired consolidated regulatory masters.

Revision ID: 0012_clean_slate_legacy
Revises: 0013_normalize_scope_ids
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0012_clean_slate_legacy"
down_revision: str | None = "0013_normalize_scope_ids"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LEGACY_TABLES = (
    "import_log", "law_compliance_area_map", "provision_compliance_area_map",
    "evidence_master", "observation_master", "audit_procedure_master",
    "compliance_requirement_master", "provision_master", "law_master",
    "compliance_area_master", "regulatory_authority_master", "origin_master",
    "enum_master", "sub_sector_master", "sector_master",
)


def upgrade() -> None:
    # This is intentionally destructive: no customer audits exist in the new launch.
    op.execute("DELETE FROM audit_evidence_attachment")
    op.execute("DELETE FROM audit_engagement_item")
    op.execute("DELETE FROM audit_engagement")
    for table_name in LEGACY_TABLES:
        op.execute(f'DROP TABLE IF EXISTS public."{table_name}" CASCADE')


def downgrade() -> None:
    raise RuntimeError("The clean-slate legacy removal cannot be reversed without a database backup.")
