"""create pharmacy regulatory master tables

Revision ID: 0001_pharmacy_regulatory
Revises:
Create Date: 2026-07-08
"""
from collections.abc import Sequence


revision: str = "0001_pharmacy_regulatory"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Retired in the clean architecture. Regulatory data is created in the
    # independently owned schemas introduced by the parallel dataset revisions.
    pass


def downgrade() -> None:
    pass
