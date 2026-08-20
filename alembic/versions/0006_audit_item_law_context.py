"""Add law context fields to audit engagement items.

Revision ID: 0006_audit_item_law_context
Revises: 0005_audit_item_metadata
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_audit_item_law_context"
down_revision = "0005_audit_item_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audit_engagement_item",
        sa.Column("authority_level", sa.String(), nullable=True),
    )
    op.add_column(
        "audit_engagement_item",
        sa.Column("applicability_type", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_audit_engagement_item_authority_level"),
        "audit_engagement_item",
        ["authority_level"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_engagement_item_applicability_type"),
        "audit_engagement_item",
        ["applicability_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_audit_engagement_item_applicability_type"),
        table_name="audit_engagement_item",
    )
    op.drop_index(
        op.f("ix_audit_engagement_item_authority_level"),
        table_name="audit_engagement_item",
    )
    op.drop_column("audit_engagement_item", "applicability_type")
    op.drop_column("audit_engagement_item", "authority_level")
