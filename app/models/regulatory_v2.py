from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    func,
)

from app.core.database import Base
# Each data source lives in its own PostgreSQL schema.  IDs in the workbooks
# are intentionally local to that schema (for example, LAW001 can exist in IT
# and Bank without a collision).
REGULATORY_DATASET_SCHEMAS = ("common_core", "pharmacy", "bank", "it", "manufacturing")


def _timestamp_columns() -> list[Column]:
    return [
        Column(
            "created_at",
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
        Column(
            "updated_at",
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    ]


def _regulatory_tables(schema_name: str) -> list[Table]:
    metadata: MetaData = Base.metadata

    sector_master = Table(
        "sector_master",
        metadata,
        Column("sector_id", String, primary_key=True),
        Column("sector_name", String, nullable=False, index=True),
        Column("description", Text),
        Column("active", String, nullable=False, index=True),
        Column("remark", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    sub_sector_master = Table(
        "sub_sector_master",
        metadata,
        Column("sub_sector_id", String, primary_key=True),
        Column(
            "sector_id",
            String,
            ForeignKey(f"{schema_name}.sector_master.sector_id"),
            nullable=False,
            index=True,
        ),
        Column("sub_sector_name", String, nullable=False, index=True),
        Column("description", Text),
        Column("active", String, nullable=False, index=True),
        *_timestamp_columns(),
        schema=schema_name,
    )

    regulatory_authority_master = Table(
        "regulatory_authority_master",
        metadata,
        Column("authority_id", String, primary_key=True),
        Column("regulatory_authority", String, nullable=False, index=True),
        Column("short_name", String, index=True),
        Column("authority_type", String, index=True),
        Column("jurisdiction", String, index=True),
        Column("parent_authority", String),
        Column("description", Text),
        Column("active", String, nullable=False, index=True),
        *_timestamp_columns(),
        schema=schema_name,
    )

    compliance_area_master = Table(
        "compliance_area_master",
        metadata,
        Column("area_id", String, primary_key=True),
        Column(
            "parent_area_id",
            String,
            ForeignKey(f"{schema_name}.compliance_area_master.area_id"),
            index=True,
        ),
        Column("parent_area", String, index=True),
        Column("compliance_area", String, nullable=False, index=True),
        Column("description", Text),
        Column("display_order", Integer),
        Column("active", String, nullable=False, index=True),
        *_timestamp_columns(),
        schema=schema_name,
    )

    origin_master = Table(
        "origin_master",
        metadata,
        Column("origin_code", String, primary_key=True),
        Column("origin_name", String, nullable=False, index=True),
        Column("description", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    enum_master = Table(
        "enum_master",
        metadata,
        Column("enum_type", String, index=True),
        Column("allowed_value", String, index=True),
        Column("description", Text),
        *_timestamp_columns(),
        PrimaryKeyConstraint("enum_type", "allowed_value", name=f"pk_{schema_name}_enum_master"),
        schema=schema_name,
    )

    law_master = Table(
        "law_master",
        metadata,
        Column("law_id", String, primary_key=True),
        Column("domain", String, nullable=False, index=True),
        Column("sector", String, nullable=False, index=True),
        Column("sub_sector", String, nullable=False, index=True),
        Column("regulator", String, nullable=False, index=True),
        Column("authority_level", String, index=True),
        Column("document_type", String, nullable=False, index=True),
        Column(
            "parent_law",
            String,
            ForeignKey(f"{schema_name}.law_master.law_id"),
            index=True,
        ),
        Column("law_name", String, nullable=False, index=True),
        Column("law_compliance_area_map", String),
        Column("applicability_type", String, nullable=False, index=True),
        Column("applicability_trigger", Text),
        Column("active", String, nullable=False, index=True),
        Column("review_frequency", String, index=True),
        Column("remarks", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    law_compliance_area_map = Table(
        "law_compliance_area_map",
        metadata,
        Column("map_id", String, primary_key=True),
        Column(
            "law_id",
            String,
            ForeignKey(f"{schema_name}.law_master.law_id"),
            nullable=False,
            index=True,
        ),
        Column(
            "compliance_area_id",
            String,
            ForeignKey(f"{schema_name}.compliance_area_master.area_id"),
            nullable=False,
            index=True,
        ),
        Column("active_status", String, nullable=False, index=True),
        Column("remarks", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    applicability_matrix = Table(
        "applicability_matrix",
        metadata,
        Column("sector", String, primary_key=True),
        Column("sub_sector", String, primary_key=True),
        Column(
            "law_id",
            String,
            ForeignKey(f"{schema_name}.law_master.law_id"),
            primary_key=True,
            index=True,
        ),
        Column("mandatory", String, index=True),
        Column("conditional", String, index=True),
        Column("applicability_trigger", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    provision_master = Table(
        "provision_master",
        metadata,
        Column("provision_id", String, primary_key=True),
        Column(
            "law_id",
            String,
            ForeignKey(f"{schema_name}.law_master.law_id"),
            nullable=False,
            index=True,
        ),
        Column(
            "sub_sector_id",
            String,
            ForeignKey(f"{schema_name}.sub_sector_master.sub_sector_id"),
            index=True,
        ),
        Column("provision_category", String, nullable=False, index=True),
        Column("statutory_reference", String, index=True),
        Column("provision_name", String, nullable=False, index=True),
        Column("provision_description", Text),
        Column(
            "origin",
            String,
            ForeignKey(f"{schema_name}.origin_master.origin_code"),
            nullable=False,
            index=True,
        ),
        Column("active", String, nullable=False, index=True),
        Column("remarks", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    provision_compliance_area_map = Table(
        "provision_compliance_area_map",
        metadata,
        Column("map_id", String, primary_key=True),
        Column(
            "provision_id",
            String,
            ForeignKey(f"{schema_name}.provision_master.provision_id"),
            nullable=False,
            index=True,
        ),
        Column(
            "compliance_area_id",
            String,
            ForeignKey(f"{schema_name}.compliance_area_master.area_id"),
            nullable=False,
            index=True,
        ),
        Column("active", String, nullable=False, index=True),
        Column("remarks", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    compliance_requirement_master = Table(
        "compliance_requirement_master",
        metadata,
        Column("compliance_id", String, primary_key=True),
        Column(
            "provision_id",
            String,
            ForeignKey(f"{schema_name}.provision_master.provision_id"),
            nullable=False,
            index=True,
        ),
        Column(
            "compliance_area_id",
            String,
            ForeignKey(f"{schema_name}.compliance_area_master.area_id"),
            nullable=False,
            index=True,
        ),
        Column("compliance_requirement", Text, nullable=False),
        Column("compliance_objective", Text),
        Column("applicability", String, index=True),
        Column("frequency", String, index=True),
        Column("due_timeline", String),
        Column("responsible_person", String, index=True),
        Column("non_compliance_consequence", Text),
        Column("priority", String, index=True),
        Column(
            "origin",
            String,
            ForeignKey(f"{schema_name}.origin_master.origin_code"),
            nullable=False,
            index=True,
        ),
        Column("active", String, nullable=False, index=True),
        Column("remarks", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    audit_procedure_master = Table(
        "audit_procedure_master",
        metadata,
        Column("audit_id", String, primary_key=True),
        Column(
            "compliance_id",
            String,
            ForeignKey(f"{schema_name}.compliance_requirement_master.compliance_id"),
            nullable=False,
            index=True,
        ),
        Column("audit_procedure", Text, nullable=False),
        Column("audit_method", String, index=True),
        Column("audit_frequency", String, index=True),
        Column(
            "origin",
            String,
            ForeignKey(f"{schema_name}.origin_master.origin_code"),
            nullable=False,
            index=True,
        ),
        Column("risk_focus", Text),
        Column("active", String, nullable=False, index=True),
        Column("remarks", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    evidence_master = Table(
        "evidence_master",
        metadata,
        Column("evidence_id", String, primary_key=True),
        Column(
            "audit_id",
            String,
            ForeignKey(f"{schema_name}.audit_procedure_master.audit_id"),
            nullable=False,
            index=True,
        ),
        Column("evidence_required", Text, nullable=False),
        Column("evidence_type", String, index=True),
        Column("mandatory", String, nullable=False, index=True),
        Column("retention_category", String, index=True),
        Column(
            "origin",
            String,
            ForeignKey(f"{schema_name}.origin_master.origin_code"),
            nullable=False,
            index=True,
        ),
        Column("active", String, nullable=False, index=True),
        Column("remarks", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    observation_master = Table(
        "observation_master",
        metadata,
        Column("observation_id", String, primary_key=True),
        Column(
            "audit_id",
            String,
            ForeignKey(f"{schema_name}.audit_procedure_master.audit_id"),
            nullable=False,
            index=True,
        ),
        Column("observation_template", Text, nullable=False),
        Column("risk_level", String, nullable=False, index=True),
        Column("recommendation", Text),
        Column("observation_category", String, index=True),
        Column(
            "origin",
            String,
            ForeignKey(f"{schema_name}.origin_master.origin_code"),
            nullable=False,
            index=True,
        ),
        Column("active", String, nullable=False, index=True),
        Column("remarks", Text),
        *_timestamp_columns(),
        schema=schema_name,
    )

    Index(
        f"ix_{schema_name}_law_sector_sub_sector",
        law_master.c.sector,
        law_master.c.sub_sector,
    )
    Index(
        f"ix_{schema_name}_applicability_scope",
        applicability_matrix.c.sector,
        applicability_matrix.c.sub_sector,
    )
    Index(
        f"ix_{schema_name}_compliance_provision_area",
        compliance_requirement_master.c.provision_id,
        compliance_requirement_master.c.compliance_area_id,
    )
    Index(
        f"ix_{schema_name}_evidence_audit_type",
        evidence_master.c.audit_id,
        evidence_master.c.evidence_type,
    )
    Index(
        f"ix_{schema_name}_observation_audit_risk",
        observation_master.c.audit_id,
        observation_master.c.risk_level,
    )

    return [
        sector_master,
        sub_sector_master,
        regulatory_authority_master,
        compliance_area_master,
        origin_master,
        enum_master,
        law_master,
        law_compliance_area_map,
        applicability_matrix,
        provision_master,
        provision_compliance_area_map,
        compliance_requirement_master,
        audit_procedure_master,
        evidence_master,
        observation_master,
    ]


REGULATORY_V2_TABLES: tuple[Table, ...] = tuple(
    table
    for schema_name in REGULATORY_DATASET_SCHEMAS
    for table in _regulatory_tables(schema_name)
)


def iter_regulatory_tables(schema_name: str | None = None) -> Iterable[Table]:
    if schema_name is None:
        return REGULATORY_V2_TABLES
    return tuple(table for table in REGULATORY_V2_TABLES if table.schema == schema_name)
