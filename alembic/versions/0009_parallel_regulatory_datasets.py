"""create parallel regulatory dataset foundation

Revision ID: 0009_parallel_regulatory_datasets
Revises: 0008_user_password_hashes
Create Date: 2026-08-20 12:20:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.models.regulatory_dataset import RegulatoryDataset
from app.models.regulatory_v2 import REGULATORY_DATASET_SCHEMAS, REGULATORY_V2_TABLES

# revision identifiers, used by Alembic.
revision: str = "0009_parallel_regulatory_datasets"
down_revision: str | None = "0008_user_password_hashes"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


DATASET_ROWS = (
    {
        "dataset_key": "common_core",
        "schema_name": "common_core",
        "display_name": "Common Corporate Core",
        "dataset_type": "Common Core",
        "description": (
            "Canonical common corporate and Companies Act universe shared across sectors "
            "through runtime composition."
        ),
        "is_active": "Yes",
    },
    {
        "dataset_key": "pharmacy",
        "schema_name": "pharmacy",
        "display_name": "Pharmacy",
        "dataset_type": "Sector",
        "description": "Independent pharmacy regulatory dataset consumed with common core at runtime.",
        "is_active": "Yes",
    },
)


def upgrade() -> None:
    bind = op.get_bind()

    RegulatoryDataset.__table__.create(bind, checkfirst=True)

    for schema_name in REGULATORY_DATASET_SCHEMAS:
        op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

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

    for table in reversed(REGULATORY_V2_TABLES):
        table.drop(bind, checkfirst=True)

    for schema_name in reversed(REGULATORY_DATASET_SCHEMAS):
        op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema_name}"'))

    RegulatoryDataset.__table__.drop(bind, checkfirst=True)
