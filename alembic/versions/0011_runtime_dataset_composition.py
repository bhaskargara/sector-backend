"""Move client and audit scope to the parallel dataset runtime.

Revision ID: 0011_runtime_composition
Revises: 0010_bank_it_parallel_datasets
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0011_runtime_composition"
down_revision: str | None = "0010_bank_it_parallel_datasets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("client_master", sa.Column("dataset_key", sa.String(), nullable=True))
    op.create_index("ix_client_master_dataset_key", "client_master", ["dataset_key"])
    op.create_foreign_key("fk_client_master_dataset_key", "client_master", "regulatory_dataset", ["dataset_key"], ["dataset_key"])

    # Existing local test clients are mapped once before the old master tables vanish.
    inspector = sa.inspect(op.get_bind())
    if "sector_master" in inspector.get_table_names(schema="public"):
        op.execute("""
            UPDATE client_master client
            SET dataset_key = CASE lower(sector.sector_name)
                WHEN 'pharmacy' THEN 'pharmacy'
                WHEN 'information technology (it)' THEN 'it'
                WHEN 'banking' THEN 'bank'
                WHEN 'non-banking financial companies' THEN 'bank'
                ELSE 'pharmacy'
            END
            FROM sector_master sector
            WHERE client.sector_id = sector.sector_id
              AND client.dataset_key IS NULL
        """)
    op.execute("UPDATE client_master SET dataset_key = 'pharmacy' WHERE dataset_key IS NULL")
    op.alter_column("client_master", "dataset_key", nullable=False)
    foreign_keys = {item["name"] for item in inspector.get_foreign_keys("client_master")}
    for constraint_name in ("client_master_sector_id_fkey", "client_master_sub_sector_id_fkey"):
        if constraint_name in foreign_keys:
            op.drop_constraint(constraint_name, "client_master", type_="foreignkey")

    op.add_column("audit_engagement", sa.Column("dataset_key", sa.String(), nullable=True))
    op.create_index("ix_audit_engagement_dataset_key", "audit_engagement", ["dataset_key"])
    op.execute("""
        UPDATE audit_engagement audit
        SET dataset_key = client.dataset_key
        FROM client_master client
        WHERE audit.client_id = client.client_id
    """)
    op.execute("UPDATE audit_engagement SET dataset_key = 'pharmacy' WHERE dataset_key IS NULL")
    op.alter_column("audit_engagement", "dataset_key", nullable=False)

    op.add_column("audit_engagement_item", sa.Column("parent_law_id", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("parent_law_name", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("source_scope", sa.String(), nullable=True))
    op.add_column("audit_engagement_item", sa.Column("dataset_key", sa.String(), nullable=True))
    op.create_index("ix_audit_engagement_item_parent_law_id", "audit_engagement_item", ["parent_law_id"])
    op.create_index("ix_audit_engagement_item_source_scope", "audit_engagement_item", ["source_scope"])
    op.create_index("ix_audit_engagement_item_dataset_key", "audit_engagement_item", ["dataset_key"])
    op.execute("""
        UPDATE audit_engagement_item item
        SET source_scope = 'SECTOR', dataset_key = audit.dataset_key
        FROM audit_engagement audit
        WHERE item.audit_id = audit.audit_id
    """)
    op.execute("UPDATE audit_engagement_item SET source_scope = 'SECTOR' WHERE source_scope IS NULL")
    op.execute("UPDATE audit_engagement_item SET dataset_key = 'pharmacy' WHERE dataset_key IS NULL")
    op.alter_column("audit_engagement_item", "source_scope", nullable=False)
    op.alter_column("audit_engagement_item", "dataset_key", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_audit_engagement_item_dataset_key", table_name="audit_engagement_item")
    op.drop_index("ix_audit_engagement_item_source_scope", table_name="audit_engagement_item")
    op.drop_index("ix_audit_engagement_item_parent_law_id", table_name="audit_engagement_item")
    op.drop_column("audit_engagement_item", "dataset_key")
    op.drop_column("audit_engagement_item", "source_scope")
    op.drop_column("audit_engagement_item", "parent_law_name")
    op.drop_column("audit_engagement_item", "parent_law_id")
    op.drop_index("ix_audit_engagement_dataset_key", table_name="audit_engagement")
    op.drop_column("audit_engagement", "dataset_key")
    op.create_foreign_key("client_master_sub_sector_id_fkey", "client_master", "sub_sector_master", ["sub_sector_id"], ["sub_sector_id"])
    op.create_foreign_key("client_master_sector_id_fkey", "client_master", "sector_master", ["sector_id"], ["sector_id"])
    op.drop_constraint("fk_client_master_dataset_key", "client_master", type_="foreignkey")
    op.drop_index("ix_client_master_dataset_key", table_name="client_master")
    op.drop_column("client_master", "dataset_key")
