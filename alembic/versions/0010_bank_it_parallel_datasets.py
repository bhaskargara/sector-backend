"""add Bank and IT parallel regulatory datasets

Revision ID: 0010_bank_it_parallel_datasets
Revises: 0009_parallel_datasets
Create Date: 2026-08-23 15:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.regulatory_dataset import RegulatoryDataset
from app.models.regulatory_v2 import REGULATORY_DATASET_SCHEMAS, REGULATORY_V2_TABLES


revision: str = "0010_bank_it_parallel_datasets"
down_revision: str | None = "0009_parallel_datasets"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


DATASET_ROWS = (
    {
        "dataset_key": "bank",
        "schema_name": "bank",
        "display_name": "Banking",
        "dataset_type": "Sector",
        "description": "Independent banking regulatory dataset composed with common core at runtime.",
        "is_active": "Yes",
    },
    {
        "dataset_key": "it",
        "schema_name": "it",
        "display_name": "Information Technology (IT)",
        "dataset_type": "Sector",
        "description": "Independent IT regulatory dataset composed with common core at runtime.",
        "is_active": "Yes",
    },
)


def upgrade() -> None:
    bind = op.get_bind()

    for schema_name in REGULATORY_DATASET_SCHEMAS:
        op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

    # checkfirst keeps this safe for installations where 0009 ran from the
    # current source tree and has already created the shared table set.
    for table in REGULATORY_V2_TABLES:
        table.create(bind, checkfirst=True)

    dataset_table = RegulatoryDataset.__table__
    for row in DATASET_ROWS:
        stmt = sa.dialects.postgresql.insert(dataset_table).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=[dataset_table.c.dataset_key],
            set_={
                "schema_name": row["schema_name"],
                "display_name": row["display_name"],
                "dataset_type": row["dataset_type"],
                "description": row["description"],
                "is_active": row["is_active"],
            },
        )
        bind.execute(stmt)


def downgrade() -> None:
    bind = op.get_bind()

    for schema_name in ("bank", "it"):
        tables = [table for table in REGULATORY_V2_TABLES if table.schema == schema_name]
        for table in reversed(tables):
            table.drop(bind, checkfirst=True)
        op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema_name}"'))

    dataset_table = RegulatoryDataset.__table__
    bind.execute(
        sa.delete(dataset_table).where(dataset_table.c.dataset_key.in_(["bank", "it"]))
    )
