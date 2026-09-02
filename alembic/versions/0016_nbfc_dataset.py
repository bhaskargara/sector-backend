"""Add the NBFC parallel regulatory dataset.

Revision ID: 0016_nbfc_dataset
Revises: 0015_manufacturing_dataset
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.regulatory_dataset import RegulatoryDataset
from app.models.regulatory_v2 import REGULATORY_V2_TABLES


revision: str = "0016_nbfc_dataset"
down_revision: str | None = "0015_manufacturing_dataset"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


DATASET_ROW = {
    "dataset_key": "nbfc",
    "schema_name": "nbfc",
    "display_name": "Non-Banking Financial Companies (NBFC)",
    "dataset_type": "Sector",
    "description": "Independent NBFC regulatory dataset composed with common core at runtime.",
    "is_active": "Yes",
}


def upgrade() -> None:
    bind = op.get_bind()
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS "nbfc"'))

    for table in REGULATORY_V2_TABLES:
        if table.schema == "nbfc":
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
        if table.schema == "nbfc":
            table.drop(bind, checkfirst=True)
    op.execute(sa.text('DROP SCHEMA IF EXISTS "nbfc"'))
    bind.execute(
        sa.delete(RegulatoryDataset.__table__).where(
            RegulatoryDataset.__table__.c.dataset_key == "nbfc"
        )
    )
