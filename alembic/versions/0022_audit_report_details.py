"""Store audit-specific report details for generated PDFs.

Revision ID: 0022_audit_report_details
Revises: 0021_official_source_links
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0022_audit_report_details"
down_revision: str | None = "0021_official_source_links"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audit_engagement",
        sa.Column(
            "report_details",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )


def downgrade() -> None:
    op.drop_column("audit_engagement", "report_details")
