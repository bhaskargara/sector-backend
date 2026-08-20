"""add password hashes to user tables

Revision ID: 0008_user_password_hashes
Revises: 0007_enterprise_engagements
Create Date: 2026-08-14 16:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_user_password_hashes"
down_revision: str | None = "0007_enterprise_engagements"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("firm_user", sa.Column("password_hash", sa.String(), nullable=True))
    op.add_column(
        "platform_admin_user",
        sa.Column("password_hash", sa.String(), nullable=True),
    )
    op.add_column("enterprise_user", sa.Column("password_hash", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("enterprise_user", "password_hash")
    op.drop_column("platform_admin_user", "password_hash")
    op.drop_column("firm_user", "password_hash")
