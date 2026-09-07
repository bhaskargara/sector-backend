"""Support multiple selected sub-sectors for a client and audit snapshot.

Revision ID: 0019_multi_sub_sector_audits
Revises: 0018_audit_locking
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "0019_multi_sub_sector_audits"
down_revision: str | None = "0018_audit_locking"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    for table_name in ("client_master", "audit_engagement"):
        op.add_column(
            table_name,
            sa.Column(
                "sub_sector_ids",
                JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )
        op.execute(
            sa.text(
                f"UPDATE {table_name} "
                "SET sub_sector_ids = jsonb_build_array(sub_sector_id) "
                "WHERE sub_sector_ids = '[]'::jsonb"
            )
        )


def downgrade() -> None:
    op.drop_column("audit_engagement", "sub_sector_ids")
    op.drop_column("client_master", "sub_sector_ids")
