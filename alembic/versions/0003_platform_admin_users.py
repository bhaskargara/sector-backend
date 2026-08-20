"""create platform admin users

Revision ID: 0003_platform_admin_users
Revises: 0002_organization_tenant
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_platform_admin_users"
down_revision: str | None = "0002_organization_tenant"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "platform_admin_user",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_platform_admin_user_email", "platform_admin_user", ["email"], unique=True)
    op.create_index("ix_platform_admin_user_role", "platform_admin_user", ["role"])
    op.create_index("ix_platform_admin_user_status", "platform_admin_user", ["status"])


def downgrade() -> None:
    op.drop_table("platform_admin_user")
