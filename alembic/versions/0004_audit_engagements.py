"""create audit engagements

Revision ID: 0004_audit_engagements
Revises: 0003_platform_admin_users
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_audit_engagements"
down_revision: str | None = "0003_platform_admin_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "audit_engagement",
        sa.Column("audit_id", sa.String(), primary_key=True),
        sa.Column("firm_id", sa.String(), sa.ForeignKey("firm_master.firm_id"), nullable=False),
        sa.Column("client_id", sa.String(), sa.ForeignKey("client_master.client_id"), nullable=False),
        sa.Column("audit_type", sa.String(), nullable=False),
        sa.Column("audit_period_label", sa.String(), nullable=False),
        sa.Column("period_start", sa.Date()),
        sa.Column("period_end", sa.Date()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("sector_id", sa.String(), nullable=False),
        sa.Column("sub_sector_id", sa.String(), nullable=False),
        sa.Column("client_name", sa.String(), nullable=False),
        sa.Column("sector_name", sa.String()),
        sa.Column("sub_sector_name", sa.String()),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remarks", sa.Text()),
        *timestamps(),
    )
    op.create_index("ix_audit_engagement_firm_id", "audit_engagement", ["firm_id"])
    op.create_index("ix_audit_engagement_client_id", "audit_engagement", ["client_id"])
    op.create_index("ix_audit_engagement_audit_type", "audit_engagement", ["audit_type"])
    op.create_index("ix_audit_engagement_audit_period_label", "audit_engagement", ["audit_period_label"])
    op.create_index("ix_audit_engagement_status", "audit_engagement", ["status"])
    op.create_index("ix_audit_engagement_sector_id", "audit_engagement", ["sector_id"])
    op.create_index("ix_audit_engagement_sub_sector_id", "audit_engagement", ["sub_sector_id"])

    op.create_table(
        "audit_engagement_item",
        sa.Column("item_id", sa.String(), primary_key=True),
        sa.Column("audit_id", sa.String(), sa.ForeignKey("audit_engagement.audit_id"), nullable=False),
        sa.Column("law_id", sa.String()),
        sa.Column("law_name", sa.String()),
        sa.Column("provision_id", sa.String()),
        sa.Column("provision_name", sa.Text()),
        sa.Column("compliance_id", sa.String()),
        sa.Column("compliance_requirement", sa.Text()),
        sa.Column("compliance_objective", sa.Text()),
        sa.Column("audit_procedure_id", sa.String()),
        sa.Column("audit_procedure", sa.Text()),
        sa.Column("audit_method", sa.String()),
        sa.Column("evidence_template", sa.Text()),
        sa.Column("observation_template", sa.Text()),
        sa.Column("priority", sa.String()),
        sa.Column("risk_level", sa.String()),
        sa.Column("origin", sa.String()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("auditor_remarks", sa.Text()),
        sa.Column("observation_notes", sa.Text()),
        sa.Column("evidence_notes", sa.Text()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
    )
    op.create_index("ix_audit_engagement_item_audit_id", "audit_engagement_item", ["audit_id"])
    op.create_index("ix_audit_engagement_item_law_id", "audit_engagement_item", ["law_id"])
    op.create_index("ix_audit_engagement_item_provision_id", "audit_engagement_item", ["provision_id"])
    op.create_index("ix_audit_engagement_item_compliance_id", "audit_engagement_item", ["compliance_id"])
    op.create_index("ix_audit_engagement_item_audit_procedure_id", "audit_engagement_item", ["audit_procedure_id"])
    op.create_index("ix_audit_engagement_item_priority", "audit_engagement_item", ["priority"])
    op.create_index("ix_audit_engagement_item_risk_level", "audit_engagement_item", ["risk_level"])
    op.create_index("ix_audit_engagement_item_origin", "audit_engagement_item", ["origin"])
    op.create_index("ix_audit_engagement_item_status", "audit_engagement_item", ["status"])

    op.create_table(
        "audit_evidence_attachment",
        sa.Column("attachment_id", sa.String(), primary_key=True),
        sa.Column("item_id", sa.String(), sa.ForeignKey("audit_engagement_item.item_id"), nullable=False),
        sa.Column("original_file_name", sa.String(), nullable=False),
        sa.Column("stored_file_name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String()),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("relative_path", sa.String(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_audit_evidence_attachment_item_id", "audit_evidence_attachment", ["item_id"])


def downgrade() -> None:
    op.drop_table("audit_evidence_attachment")
    op.drop_table("audit_engagement_item")
    op.drop_table("audit_engagement")
