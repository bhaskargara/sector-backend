"""add enterprise and engagement foundation

Revision ID: 0007_enterprise_engagements
Revises: 0006_audit_item_law_context
Create Date: 2026-07-26
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op


revision: str = "0007_enterprise_engagements"
down_revision: str | None = "0006_audit_item_law_context"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def upgrade() -> None:
    op.create_table(
        "enterprise_master",
        sa.Column("enterprise_id", sa.String(), primary_key=True),
        sa.Column("enterprise_name", sa.String(), nullable=False),
        sa.Column("legal_name", sa.String()),
        sa.Column("contact_email", sa.String()),
        sa.Column("phone", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("remarks", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_enterprise_master_enterprise_name", "enterprise_master", ["enterprise_name"])
    op.create_index("ix_enterprise_master_legal_name", "enterprise_master", ["legal_name"])
    op.create_index("ix_enterprise_master_contact_email", "enterprise_master", ["contact_email"])
    op.create_index("ix_enterprise_master_city", "enterprise_master", ["city"])
    op.create_index("ix_enterprise_master_status", "enterprise_master", ["status"])

    op.create_table(
        "enterprise_user",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column(
            "enterprise_id",
            sa.String(),
            sa.ForeignKey("enterprise_master.enterprise_id"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_enterprise_user_enterprise_id", "enterprise_user", ["enterprise_id"])
    op.create_index("ix_enterprise_user_email", "enterprise_user", ["email"], unique=True)
    op.create_index("ix_enterprise_user_role", "enterprise_user", ["role"])
    op.create_index("ix_enterprise_user_status", "enterprise_user", ["status"])

    op.create_table(
        "firm_enterprise_engagement",
        sa.Column("engagement_id", sa.String(), primary_key=True),
        sa.Column("firm_id", sa.String(), sa.ForeignKey("firm_master.firm_id"), nullable=False),
        sa.Column(
            "enterprise_id",
            sa.String(),
            sa.ForeignKey("enterprise_master.enterprise_id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("invited_by_side", sa.String()),
        sa.Column("invited_by_user_id", sa.String()),
        sa.Column("engagement_name", sa.String()),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("remarks", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_firm_enterprise_engagement_firm_id", "firm_enterprise_engagement", ["firm_id"])
    op.create_index(
        "ix_firm_enterprise_engagement_enterprise_id",
        "firm_enterprise_engagement",
        ["enterprise_id"],
    )
    op.create_index("ix_firm_enterprise_engagement_status", "firm_enterprise_engagement", ["status"])
    op.create_index(
        "ix_firm_enterprise_engagement_invited_by_side",
        "firm_enterprise_engagement",
        ["invited_by_side"],
    )
    op.create_index(
        "ix_firm_enterprise_engagement_invited_by_user_id",
        "firm_enterprise_engagement",
        ["invited_by_user_id"],
    )
    op.create_index(
        "ix_firm_enterprise_engagement_engagement_name",
        "firm_enterprise_engagement",
        ["engagement_name"],
    )

    op.add_column("client_master", sa.Column("enterprise_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_client_master_enterprise_id",
        "client_master",
        "enterprise_master",
        ["enterprise_id"],
        ["enterprise_id"],
    )
    op.create_index("ix_client_master_enterprise_id", "client_master", ["enterprise_id"])

    op.add_column("audit_engagement", sa.Column("engagement_id", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_audit_engagement_engagement_id",
        "audit_engagement",
        "firm_enterprise_engagement",
        ["engagement_id"],
        ["engagement_id"],
    )
    op.create_index("ix_audit_engagement_engagement_id", "audit_engagement", ["engagement_id"])

    bind = op.get_bind()
    metadata = sa.MetaData()
    metadata.bind = bind

    client_master = sa.Table(
        "client_master",
        metadata,
        sa.Column("client_id", sa.String()),
        sa.Column("firm_id", sa.String()),
        sa.Column("client_name", sa.String()),
        sa.Column("legal_name", sa.String()),
        sa.Column("contact_email", sa.String()),
        sa.Column("phone", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("status", sa.String()),
        sa.Column("remarks", sa.Text()),
        sa.Column("enterprise_id", sa.String()),
    )
    enterprise_master = sa.Table(
        "enterprise_master",
        metadata,
        sa.Column("enterprise_id", sa.String()),
        sa.Column("enterprise_name", sa.String()),
        sa.Column("legal_name", sa.String()),
        sa.Column("contact_email", sa.String()),
        sa.Column("phone", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("status", sa.String()),
        sa.Column("remarks", sa.Text()),
    )
    engagement_table = sa.Table(
        "firm_enterprise_engagement",
        metadata,
        sa.Column("engagement_id", sa.String()),
        sa.Column("firm_id", sa.String()),
        sa.Column("enterprise_id", sa.String()),
        sa.Column("status", sa.String()),
        sa.Column("invited_by_side", sa.String()),
        sa.Column("invited_by_user_id", sa.String()),
        sa.Column("engagement_name", sa.String()),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("remarks", sa.Text()),
    )
    audit_engagement = sa.Table(
        "audit_engagement",
        metadata,
        sa.Column("audit_id", sa.String()),
        sa.Column("client_id", sa.String()),
        sa.Column("engagement_id", sa.String()),
    )

    client_rows = bind.execute(
        sa.select(
            client_master.c.client_id,
            client_master.c.firm_id,
            client_master.c.client_name,
            client_master.c.legal_name,
            client_master.c.contact_email,
            client_master.c.phone,
            client_master.c.city,
            client_master.c.status,
            client_master.c.remarks,
            client_master.c.enterprise_id,
        )
    ).mappings().all()

    client_to_engagement: dict[str, str] = {}
    for client in client_rows:
        enterprise_id = client["enterprise_id"] or _new_id("ENT")
        bind.execute(
            enterprise_master.insert().values(
                enterprise_id=enterprise_id,
                enterprise_name=client["client_name"],
                legal_name=client["legal_name"],
                contact_email=client["contact_email"],
                phone=client["phone"],
                city=client["city"],
                status=client["status"] or "Active",
                remarks=client["remarks"],
            )
        )
        bind.execute(
            client_master.update()
            .where(client_master.c.client_id == client["client_id"])
            .values(enterprise_id=enterprise_id)
        )

        engagement_id = _new_id("ENG")
        bind.execute(
            engagement_table.insert().values(
                engagement_id=engagement_id,
                firm_id=client["firm_id"],
                enterprise_id=enterprise_id,
                status="Active",
                invited_by_side="Firm",
                invited_by_user_id=None,
                engagement_name=client["client_name"],
                start_date=None,
                end_date=None,
                remarks="Backfilled from existing client_master",
            )
        )
        client_to_engagement[client["client_id"]] = engagement_id

    for client_id, engagement_id in client_to_engagement.items():
        bind.execute(
            audit_engagement.update()
            .where(audit_engagement.c.client_id == client_id)
            .values(engagement_id=engagement_id)
        )


def downgrade() -> None:
    op.drop_index("ix_audit_engagement_engagement_id", table_name="audit_engagement")
    op.drop_constraint("fk_audit_engagement_engagement_id", "audit_engagement", type_="foreignkey")
    op.drop_column("audit_engagement", "engagement_id")

    op.drop_index("ix_client_master_enterprise_id", table_name="client_master")
    op.drop_constraint("fk_client_master_enterprise_id", "client_master", type_="foreignkey")
    op.drop_column("client_master", "enterprise_id")

    op.drop_table("firm_enterprise_engagement")
    op.drop_table("enterprise_user")
    op.drop_table("enterprise_master")
