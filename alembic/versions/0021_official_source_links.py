"""Add official regulatory-source links to master data and audit snapshots.

Revision ID: 0021_official_source_links
Revises: 0020_scope_classification
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0021_official_source_links"
down_revision: str | None = "0020_scope_classification"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


MCA_COMPANIES_ACT_URL = (
    "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/acts.html?act=NTk2MQ=="
)
DATASET_SCHEMAS = (
    "common_core",
    "pharmacy",
    "bank",
    "it",
    "manufacturing",
    "nbfc",
    "sebi_listed",
)


def upgrade() -> None:
    # A clean install uses current regulatory metadata in earlier migrations.
    # PostgreSQL's IF NOT EXISTS therefore also makes this migration safe there.
    for schema_name in DATASET_SCHEMAS:
        op.execute(
            sa.text(
                f"ALTER TABLE {schema_name}.law_master "
                "ADD COLUMN IF NOT EXISTS official_source_url TEXT"
            )
        )
    op.execute(
        sa.text(
            "ALTER TABLE audit_engagement_item "
            "ADD COLUMN IF NOT EXISTS official_source_url TEXT"
        )
    )

    # The supplied frozen workbook has no source-link column. Seed the
    # authoritative MCA Companies Act page without modifying that workbook.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE common_core.law_master
            SET official_source_url = :source_url
            WHERE lower(trim(law_name)) = 'companies act, 2013'
            """
        ),
        {"source_url": MCA_COMPANIES_ACT_URL},
    )
    bind.execute(
        sa.text(
            """
            UPDATE audit_engagement_item AS item
            SET official_source_url = law.official_source_url
            FROM common_core.law_master AS law
            WHERE item.dataset_key = 'common_core'
              AND item.law_id = law.law_id
              AND law.official_source_url IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.execute("ALTER TABLE audit_engagement_item DROP COLUMN IF EXISTS official_source_url")
    for schema_name in DATASET_SCHEMAS:
        op.execute(
            sa.text(
                f"ALTER TABLE {schema_name}.law_master "
                "DROP COLUMN IF EXISTS official_source_url"
            )
        )
