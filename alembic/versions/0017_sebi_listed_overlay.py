"""Add listed-company profile support and the SEBI overlay dataset.

Revision ID: 0017_sebi_listed_overlay
Revises: 0016_nbfc_dataset
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.regulatory_dataset import RegulatoryDataset
from app.models.regulatory_v2 import REGULATORY_V2_TABLES


revision: str = "0017_sebi_listed_overlay"
down_revision: str | None = "0016_nbfc_dataset"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


DATASET_ROW = {
    "dataset_key": "sebi_listed",
    "schema_name": "sebi_listed",
    "display_name": "SEBI Listed Entity Overlay",
    "dataset_type": "Overlay",
    "description": "Conditional SEBI overlay applied only to clients marked as listed companies.",
    "is_active": "Yes",
}


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "client_master",
        sa.Column(
            "is_listed_company",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(
        "ix_client_master_is_listed_company",
        "client_master",
        ["is_listed_company"],
    )
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS "sebi_listed"'))

    for table in REGULATORY_V2_TABLES:
        if table.schema == "sebi_listed":
            table.create(bind, checkfirst=True)

    dataset_table = RegulatoryDataset.__table__
    stmt = sa.dialects.postgresql.insert(dataset_table).values(**DATASET_ROW)
    stmt = stmt.on_conflict_do_update(
        index_elements=[dataset_table.c.dataset_key],
        set_={
            "schema_name": DATASET_ROW["schema_name"],
            "display_name": DATASET_ROW["display_name"],
            "dataset_type": DATASET_ROW["dataset_type"],
            "description": DATASET_ROW["description"],
            "is_active": DATASET_ROW["is_active"],
        },
    )
    bind.execute(stmt)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(REGULATORY_V2_TABLES):
        if table.schema == "sebi_listed":
            table.drop(bind, checkfirst=True)
    op.execute(sa.text('DROP SCHEMA IF EXISTS "sebi_listed"'))
    bind.execute(
        sa.delete(RegulatoryDataset.__table__).where(
            RegulatoryDataset.__table__.c.dataset_key == "sebi_listed"
        )
    )
    op.drop_index("ix_client_master_is_listed_company", table_name="client_master")
    op.drop_column("client_master", "is_listed_company")
