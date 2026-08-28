"""Add the Manufacturing parallel regulatory dataset.

Revision ID: 0015_manufacturing_dataset
Revises: 0014_item_scope
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models.regulatory_dataset import RegulatoryDataset
from app.models.regulatory_v2 import REGULATORY_V2_TABLES


revision: str = "0015_manufacturing_dataset"
down_revision: str | None = "0014_item_scope"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


DATASET_ROW = {
    "dataset_key": "manufacturing",
    "schema_name": "manufacturing",
    "display_name": "Manufacturing",
    "dataset_type": "Sector",
    "description": "Independent manufacturing regulatory dataset composed with common core at runtime.",
    "is_active": "Yes",
}


def upgrade() -> None:
    bind = op.get_bind()
    op.execute(sa.text('CREATE SCHEMA IF NOT EXISTS "manufacturing"'))

    for table in REGULATORY_V2_TABLES:
        if table.schema == "manufacturing":
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
        if table.schema == "manufacturing":
            table.drop(bind, checkfirst=True)
    op.execute(sa.text('DROP SCHEMA IF EXISTS "manufacturing"'))
    bind.execute(
        sa.delete(RegulatoryDataset.__table__).where(
            RegulatoryDataset.__table__.c.dataset_key == "manufacturing"
        )
    )
