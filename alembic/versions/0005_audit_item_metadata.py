"""add audit item metadata

Revision ID: 0005_audit_item_metadata
Revises: 0004_audit_engagements
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_audit_item_metadata"
down_revision: str | None = "0004_audit_engagements"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audit_engagement_item", sa.Column("regulator", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("document_type", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("applicability_trigger", sa.Text(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("statutory_reference", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("compliance_frequency", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("audit_frequency", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("evidence_type", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("evidence_mandatory", sa.String(), nullable=True))
    op.create_index("ix_audit_engagement_item_regulator", "audit_engagement_item", ["regulator"])
    op.create_index("ix_audit_engagement_item_document_type", "audit_engagement_item", ["document_type"])
    op.create_index("ix_audit_engagement_item_statutory_reference", "audit_engagement_item", ["statutory_reference"])
    op.create_index("ix_audit_engagement_item_compliance_frequency", "audit_engagement_item", ["compliance_frequency"])
    op.create_index("ix_audit_engagement_item_audit_frequency", "audit_engagement_item", ["audit_frequency"])
    op.create_index("ix_audit_engagement_item_evidence_type", "audit_engagement_item", ["evidence_type"])
    op.create_index("ix_audit_engagement_item_evidence_mandatory", "audit_engagement_item", ["evidence_mandatory"])


def downgrade() -> None:
    op.drop_index("ix_audit_engagement_item_evidence_mandatory", table_name="audit_engagement_item")
    op.drop_index("ix_audit_engagement_item_evidence_type", table_name="audit_engagement_item")
    op.drop_index("ix_audit_engagement_item_audit_frequency", table_name="audit_engagement_item")
    op.drop_index("ix_audit_engagement_item_compliance_frequency", table_name="audit_engagement_item")
    op.drop_index("ix_audit_engagement_item_statutory_reference", table_name="audit_engagement_item")
    op.drop_index("ix_audit_engagement_item_document_type", table_name="audit_engagement_item")
    op.drop_index("ix_audit_engagement_item_regulator", table_name="audit_engagement_item")
    op.drop_column("audit_engagement_item", "evidence_mandatory")
    op.drop_column("audit_engagement_item", "evidence_type")
    op.drop_column("audit_engagement_item", "audit_frequency")
    op.drop_column("audit_engagement_item", "compliance_frequency")
    op.drop_column("audit_engagement_item", "statutory_reference")
    op.drop_column("audit_engagement_item", "applicability_trigger")
    op.drop_column("audit_engagement_item", "document_type")
    op.drop_column("audit_engagement_item", "regulator")
