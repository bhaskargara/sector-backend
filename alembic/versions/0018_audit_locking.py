"""Add Platform Admin audit finalization fields.

Revision ID: 0018_audit_locking
Revises: 0017_sebi_listed_overlay
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0018_audit_locking"
down_revision: str | None = "0017_sebi_listed_overlay"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audit_engagement",
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "audit_engagement",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_audit_engagement_is_locked", "audit_engagement", ["is_locked"])


def downgrade() -> None:
    op.drop_index("ix_audit_engagement_is_locked", table_name="audit_engagement")
    op.drop_column("audit_engagement", "locked_at")
    op.drop_column("audit_engagement", "is_locked")
