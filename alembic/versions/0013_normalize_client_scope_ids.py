"""Normalize retained client scope IDs to their selected dataset namespace.

Revision ID: 0013_normalize_scope_ids
Revises: 0011_runtime_composition
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0013_normalize_scope_ids"
down_revision: str | None = "0011_runtime_composition"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The earlier consolidated database prefixed IDs (for example PHA-SEC001).
    # Parallel schemas deliberately retain the workbook-local SEC001/SUB001 IDs.
    op.execute("""
        UPDATE client_master
        SET sector_id = regexp_replace(sector_id, '^[A-Z]+-', '')
        WHERE dataset_key IN ('pharmacy', 'it', 'bank')
    """)
    op.execute("""
        UPDATE client_master
        SET sub_sector_id = regexp_replace(sub_sector_id, '^[A-Z]+-', '')
        WHERE dataset_key IN ('pharmacy', 'it', 'bank')
    """)


def downgrade() -> None:
    pass
