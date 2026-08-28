"""Runtime composition for the independently owned regulatory datasets."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.regulatory_dataset import RegulatoryDataset
from app.models.regulatory_v2 import iter_regulatory_tables


@dataclass(frozen=True)
class RegulatoryScope:
    dataset_key: str
    sector_id: str
    sector_name: str
    sub_sector_id: str
    sub_sector_name: str


def _tables(schema_name: str):
    return {table.name: table for table in iter_regulatory_tables(schema_name)}


def get_dataset(db: Session, dataset_key: str) -> RegulatoryDataset | None:
    return db.get(RegulatoryDataset, dataset_key)


def list_datasets(db: Session) -> list[RegulatoryDataset]:
    return db.scalars(
        select(RegulatoryDataset)
        .where(RegulatoryDataset.dataset_key != "common_core", RegulatoryDataset.is_active == "Yes")
        .order_by(RegulatoryDataset.display_name)
    ).all()


def get_scope(
    db: Session, dataset_key: str, sector_id: str, sub_sector_id: str
) -> RegulatoryScope | None:
    dataset = get_dataset(db, dataset_key)
    if not dataset or dataset.dataset_key == "common_core" or dataset.is_active != "Yes":
        return None
    tables = _tables(dataset.schema_name)
    sector = db.execute(
        select(tables["sector_master"]).where(tables["sector_master"].c.sector_id == sector_id)
    ).mappings().first()
    sub_sector = db.execute(
        select(tables["sub_sector_master"]).where(
            tables["sub_sector_master"].c.sub_sector_id == sub_sector_id,
            tables["sub_sector_master"].c.sector_id == sector_id,
        )
    ).mappings().first()
    if not sector or not sub_sector:
        return None
    return RegulatoryScope(
        dataset_key=dataset_key,
        sector_id=sector_id,
        sector_name=sector["sector_name"],
        sub_sector_id=sub_sector_id,
        sub_sector_name=sub_sector["sub_sector_name"],
    )


def list_sectors(db: Session, dataset_key: str | None = None) -> list[dict[str, str | None]]:
    datasets = [get_dataset(db, dataset_key)] if dataset_key else list_datasets(db)
    result: list[dict[str, str | None]] = []
    for dataset in datasets:
        if not dataset:
            continue
        table = _tables(dataset.schema_name)["sector_master"]
        for row in db.execute(select(table).order_by(table.c.sector_name)).mappings():
            result.append({
                "dataset_key": dataset.dataset_key,
                "sector_id": row["sector_id"],
                "sector_name": row["sector_name"],
                "description": row["description"],
                "active": row["active"],
                "remark": row["remark"],
            })
    return result


def list_sub_sectors(db: Session, dataset_key: str, sector_id: str) -> list[dict[str, str | None]]:
    dataset = get_dataset(db, dataset_key)
    if not dataset:
        return []
    table = _tables(dataset.schema_name)["sub_sector_master"]
    return [
        {"dataset_key": dataset_key, **dict(row)}
        for row in db.execute(
            select(table).where(table.c.sector_id == sector_id).order_by(table.c.sub_sector_name)
        ).mappings()
    ]


def _canonical_core_law_names(db: Session) -> set[str]:
    table = _tables("common_core")["law_master"]
    return set(db.scalars(select(table.c.law_name)).all())


def compose_control_rows(db: Session, scope: RegulatoryScope) -> list[dict[str, object]]:
    """Return audit-ready rows from Common Core plus exactly one sector dataset.

    Identical law titles in a sector workbook are intentionally excluded when a
    canonical Common Core version exists, so Companies Act controls are never
    duplicated in a sector audit.
    """
    canonical_core_names = _canonical_core_law_names(db)
    sources = [("common_core", "COMMON_CORE"), (scope.dataset_key, "SECTOR")]
    result: list[dict[str, object]] = []

    for dataset_key, source_scope in sources:
        dataset = get_dataset(db, dataset_key)
        if not dataset:
            continue
        tables = _tables(dataset.schema_name)
        law = tables["law_master"]
        provision = tables["provision_master"]
        compliance = tables["compliance_requirement_master"]
        audit = tables["audit_procedure_master"]
        law_names = dict(db.execute(select(law.c.law_id, law.c.law_name)).all())

        law_scope = [law.c.active == "Yes"]
        provision_scope = [provision.c.active == "Yes"]
        if source_scope == "SECTOR":
            law_scope.append(or_(law.c.sub_sector == "All", law.c.sub_sector == scope.sub_sector_name))
            provision_scope.append(or_(provision.c.sub_sector_id.is_(None), provision.c.sub_sector_id == scope.sub_sector_id))
        # Common Corporate Core is global by design. Its workbook uses its own
        # applicability label rather than a selected sector's sub-sector name.

        statement = (
            select(law, provision, compliance, audit)
            .join(provision, and_(provision.c.law_id == law.c.law_id, *provision_scope))
            .outerjoin(compliance, compliance.c.provision_id == provision.c.provision_id)
            .outerjoin(audit, audit.c.compliance_id == compliance.c.compliance_id)
            .where(*law_scope)
            .order_by(law.c.law_id, provision.c.provision_id, compliance.c.compliance_id, audit.c.audit_id)
        )
        for row in db.execute(statement).mappings():
            if source_scope == "SECTOR" and row[law.c.law_name] in canonical_core_names:
                continue
            applicability_scope = (
                "COMMON_CORE"
                if source_scope == "COMMON_CORE"
                else "SUB_SECTOR"
                if row[provision.c.sub_sector_id] == scope.sub_sector_id
                else "SECTOR_WIDE"
            )
            result.append({
                "source_scope": source_scope,
                "applicability_scope": applicability_scope,
                "dataset_key": dataset_key,
                "law_id": row[law.c.law_id],
                "parent_law_id": row[law.c.parent_law],
                "parent_law_name": law_names.get(row[law.c.parent_law]),
                "law_name": row[law.c.law_name],
                "regulator": row[law.c.regulator],
                "authority_level": row[law.c.authority_level],
                "document_type": row[law.c.document_type],
                "applicability_type": row[law.c.applicability_type],
                "applicability_trigger": row[law.c.applicability_trigger],
                "provision_id": row[provision.c.provision_id],
                "provision_name": row[provision.c.provision_name],
                "statutory_reference": row[provision.c.statutory_reference],
                "origin": row[provision.c.origin],
                "compliance_id": row[compliance.c.compliance_id],
                "compliance_requirement": row[compliance.c.compliance_requirement],
                "compliance_objective": row[compliance.c.compliance_objective],
                "compliance_frequency": row[compliance.c.frequency],
                "priority": row[compliance.c.priority],
                "audit_procedure_id": row[audit.c.audit_id],
                "audit_procedure": row[audit.c.audit_procedure],
                "audit_method": row[audit.c.audit_method],
                "audit_frequency": row[audit.c.audit_frequency],
            })

    _append_evidence_and_observations(db, result)
    return result


def _append_evidence_and_observations(db: Session, rows: list[dict[str, object]]) -> None:
    by_source: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        row.update(
            {
                "evidence_template": None,
                "evidence_type": None,
                "evidence_mandatory": None,
                "observation_template": None,
                "risk_level": None,
            }
        )
        if row["audit_procedure_id"]:
            by_source[(str(row["dataset_key"]), str(row["audit_procedure_id"]))].append(row)
    for (dataset_key, audit_id), target_rows in by_source.items():
        dataset = get_dataset(db, dataset_key)
        if not dataset:
            continue
        tables = _tables(dataset.schema_name)
        evidence = db.execute(select(tables["evidence_master"]).where(tables["evidence_master"].c.audit_id == audit_id)).mappings()
        observations = db.execute(select(tables["observation_master"]).where(tables["observation_master"].c.audit_id == audit_id)).mappings()
        evidence_rows = list(evidence)
        observation_rows = list(observations)
        templates = "\n".join(_unique_nonempty_values(
            row["evidence_required"] for row in evidence_rows
        )) or None
        evidence_type = next((row["evidence_type"] for row in evidence_rows if row["evidence_type"]), None)
        mandatory = "Yes" if any(row["mandatory"] == "Yes" for row in evidence_rows) else next((row["mandatory"] for row in evidence_rows if row["mandatory"]), None)
        observation_template = "\n".join(_unique_nonempty_values(
            row["observation_template"] for row in observation_rows
        )) or None
        rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        risk_level = max((row["risk_level"] for row in observation_rows), key=lambda value: rank.get(value, 0), default=None)
        for target in target_rows:
            target.update({"evidence_template": templates, "evidence_type": evidence_type, "evidence_mandatory": mandatory, "observation_template": observation_template, "risk_level": risk_level})


def _unique_nonempty_values(values: Iterable[object]) -> list[str]:
    """Return distinct master-data text in its original workbook order."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
