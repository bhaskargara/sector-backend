"""create organization tenant foundation

Revision ID: 0002_organization_tenant
Revises: 0001_pharmacy_regulatory
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_organization_tenant"
down_revision: str | None = "0001_pharmacy_regulatory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "firm_master",
        sa.Column("firm_id", sa.String(), primary_key=True),
        sa.Column("firm_name", sa.String(), nullable=False),
        sa.Column("owner_name", sa.String()),
        sa.Column("contact_email", sa.String()),
        sa.Column("phone", sa.String()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("remarks", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_firm_master_firm_name", "firm_master", ["firm_name"])
    op.create_index("ix_firm_master_contact_email", "firm_master", ["contact_email"])
    op.create_index("ix_firm_master_status", "firm_master", ["status"])

    op.create_table(
        "firm_user",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("firm_id", sa.String(), sa.ForeignKey("firm_master.firm_id"), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_firm_user_firm_id", "firm_user", ["firm_id"])
    op.create_index("ix_firm_user_email", "firm_user", ["email"], unique=True)
    op.create_index("ix_firm_user_role", "firm_user", ["role"])
    op.create_index("ix_firm_user_status", "firm_user", ["status"])

    op.create_table(
        "client_master",
        sa.Column("client_id", sa.String(), primary_key=True),
        sa.Column("firm_id", sa.String(), sa.ForeignKey("firm_master.firm_id"), nullable=False),
        sa.Column("client_name", sa.String(), nullable=False),
        sa.Column("legal_name", sa.String()),
        sa.Column("contact_email", sa.String()),
        sa.Column("phone", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("sector_id", sa.String(), nullable=False),
        sa.Column("sub_sector_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("remarks", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_client_master_firm_id", "client_master", ["firm_id"])
    op.create_index("ix_client_master_client_name", "client_master", ["client_name"])
    op.create_index("ix_client_master_legal_name", "client_master", ["legal_name"])
    op.create_index("ix_client_master_contact_email", "client_master", ["contact_email"])
    op.create_index("ix_client_master_city", "client_master", ["city"])
    op.create_index("ix_client_master_sector_id", "client_master", ["sector_id"])
    op.create_index("ix_client_master_sub_sector_id", "client_master", ["sub_sector_id"])
    op.create_index("ix_client_master_status", "client_master", ["status"])


def downgrade() -> None:
    op.drop_table("client_master")
    op.drop_table("firm_user")
    op.drop_table("firm_master")
