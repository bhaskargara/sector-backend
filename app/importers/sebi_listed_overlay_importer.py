"""Import the frozen SEBI Listed Entity production overlay workbook.

The SEBI source uses its own `PROD ... Master` tabs and permanent identifiers,
so it is intentionally kept separate from the standard sector workbook parser.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import SessionLocal
from app.importers.pharmacy_dataset_importer import ImportSummary
from app.models.audit import AuditEngagementItem
from app.models.regulatory_v2 import iter_regulatory_tables


SEBI_DATASET_KEY = "sebi_listed"
SEBI_SECTOR_ID = "SEBI-LISTED-ENTITY"
SEBI_SUB_SECTOR_ID = "SEBI-LISTED-COMPANY"
SEBI_ORIGIN = "SEBI"
SEBI_AREA_PREFIX = "SEBI-AREA-"

SOURCE_SHEETS = {
    "laws": "PROD Law Master",
    "provisions": "PROD Provision Master",
    "compliance": "PROD Compliance Master",
    "audits": "PROD Audit Master",
    "evidence": "PROD Evidence Master",
    "observations": "PROD Observation Master",
}

TABLE_ORDER = [
    "sector_master",
    "sub_sector_master",
    "regulatory_authority_master",
    "compliance_area_master",
    "origin_master",
    "enum_master",
    "law_master",
    "law_compliance_area_map",
    "applicability_matrix",
    "provision_master",
    "provision_compliance_area_map",
    "compliance_requirement_master",
    "audit_procedure_master",
    "evidence_master",
    "observation_master",
]


def _value(record: dict[str, Any], column: str, default: str | None = None) -> str | None:
    value = record.get(column)
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return text or default


def _read_source(path: Path, sheet_name: str) -> list[dict[str, Any]]:
    # The frozen production tabs have a title, description, and blank row
    # above the actual header row.
    frame = pd.read_excel(path, sheet_name=sheet_name, header=3, dtype=object)
    return frame.dropna(how="all").to_dict(orient="records")


def _upsert_rows(db, table, rows: list[dict[str, Any]], mode: str) -> int:
    if not rows:
        return 0
    if mode == "truncate":
        db.execute(table.insert(), rows)
        return len(rows)

    statement = pg_insert(table).values(rows)
    primary_key_columns = {column.name for column in table.primary_key.columns}
    updates = {
        column.name: statement.excluded[column.name]
        for column in table.columns
        if column.name not in primary_key_columns and column.name != "created_at"
    }
    db.execute(statement.on_conflict_do_update(index_elements=list(primary_key_columns), set_=updates))
    return len(rows)


def import_sebi_listed_overlay(workbook_path: str, mode: str = "upsert") -> ImportSummary:
    if mode not in {"upsert", "truncate"}:
        raise ValueError("mode must be 'upsert' or 'truncate'")

    path = Path(workbook_path)
    if not path.is_file():
        raise FileNotFoundError(path)

    workbook_sheets = set(pd.ExcelFile(path, engine="openpyxl").sheet_names)
    missing = [sheet_name for sheet_name in SOURCE_SHEETS.values() if sheet_name not in workbook_sheets]
    if missing:
        raise ValueError(f"Missing required SEBI production sheets: {', '.join(missing)}")

    source = {key: _read_source(path, sheet) for key, sheet in SOURCE_SHEETS.items()}
    tables = {table.name: table for table in iter_regulatory_tables(SEBI_DATASET_KEY)}
    summary = ImportSummary(workbook_path=str(path), mode=mode)

    area_names = sorted(
        {
            _value(record, "Compliance Area", "SEBI compliance")
            for records in (source["provisions"], source["compliance"])
            for record in records
        }
    )
    area_ids = {area_name: f"{SEBI_AREA_PREFIX}{index:03d}" for index, area_name in enumerate(area_names, 1)}
    provision_area_by_id = {
        _value(record, "Production Provision ID"): area_ids[_value(record, "Compliance Area", "SEBI compliance")]
        for record in source["provisions"]
    }
    compliance_area_by_id = {
        _value(record, "Production Compliance ID"): area_ids[_value(record, "Compliance Area", "SEBI compliance")]
        for record in source["compliance"]
    }
    law_area_pairs = {
        (
            _value(record, "Production Law ID"),
            provision_area_by_id[_value(record, "Production Provision ID")],
        )
        for record in source["provisions"]
    }

    records: dict[str, list[dict[str, Any]]] = {
        "sector_master": [{
            "sector_id": SEBI_SECTOR_ID,
            "sector_name": "SEBI Listed Entity Overlay",
            "description": "Conditional overlay for clients marked as listed companies.",
            "active": "Yes",
            "remark": "Applied at audit creation only when the client is listed.",
        }],
        "sub_sector_master": [{
            "sub_sector_id": SEBI_SUB_SECTOR_ID,
            "sector_id": SEBI_SECTOR_ID,
            "sub_sector_name": "Listed Companies",
            "description": "SEBI overlay profile.",
            "active": "Yes",
        }],
        "regulatory_authority_master": [{
            "authority_id": "SEBI",
            "regulatory_authority": "Securities and Exchange Board of India",
            "short_name": "SEBI",
            "authority_type": "Securities regulator",
            "jurisdiction": "India",
            "parent_authority": None,
            "description": "SEBI listed entity regulatory overlay.",
            "active": "Yes",
        }],
        "compliance_area_master": [
            {
                "area_id": area_ids[name],
                "parent_area_id": None,
                "parent_area": "SEBI Listed Entity",
                "compliance_area": name,
                "description": None,
                "display_order": index,
                "active": "Yes",
            }
            for index, name in enumerate(area_names, 1)
        ],
        "origin_master": [{
            "origin_code": SEBI_ORIGIN,
            "origin_name": "SEBI Listed Entity Overlay",
            "description": "Frozen SEBI production overlay.",
        }],
        "enum_master": [],
        "law_master": [
            {
                "law_id": _value(record, "Production Law ID"),
                "domain": "SEBI Listed Entity",
                "sector": "SEBI Listed Entity Overlay",
                "sub_sector": "All",
                "regulator": "SEBI",
                "authority_level": "National",
                "document_type": "SEBI Act / Regulation / Circular",
                "parent_law": None,
                "law_name": _value(record, "Current Instrument"),
                "official_source_url": _value(record, "Official Source URL"),
                "law_compliance_area_map": None,
                "applicability_type": "Conditional",
                "applicability_trigger": _value(record, "Activation Gate"),
                "active": "Yes",
                "review_frequency": None,
                "remarks": None,
            }
            for record in source["laws"]
        ],
        "law_compliance_area_map": [
            {
                "map_id": f"SEBI-LCAM-{index:04d}",
                "law_id": law_id,
                "compliance_area_id": area_id,
                "active_status": "Yes",
                "remarks": "Derived from frozen SEBI production provision mapping.",
            }
            for index, (law_id, area_id) in enumerate(sorted(law_area_pairs), 1)
        ],
        "applicability_matrix": [],
        "provision_master": [
            {
                "provision_id": provision_id,
                "law_id": _value(record, "Production Law ID"),
                "sub_sector_id": None,
                "provision_category": "SEBI listed entity obligation",
                "statutory_reference": _value(record, "Provision Reference"),
                "provision_name": _value(record, "Atomic Obligation"),
                "provision_description": _value(record, "Boundary / Exclusion"),
                "origin": SEBI_ORIGIN,
                "active": "Yes",
                "remarks": _value(record, "Official Source URL"),
            }
            for record in source["provisions"]
            if (provision_id := _value(record, "Production Provision ID"))
        ],
        "provision_compliance_area_map": [
            {
                "map_id": f"SEBI-PCAM-{index:04d}",
                "provision_id": provision_id,
                "compliance_area_id": area_id,
                "active": "Yes",
                "remarks": "Derived from frozen SEBI production provision mapping.",
            }
            for index, (provision_id, area_id) in enumerate(sorted(provision_area_by_id.items()), 1)
        ],
        "compliance_requirement_master": [
            {
                "compliance_id": compliance_id,
                "provision_id": _value(record, "Production Provision ID"),
                "compliance_area_id": compliance_area_by_id[compliance_id],
                "compliance_requirement": _value(record, "Compliance Requirement"),
                "compliance_objective": None,
                "applicability": _value(record, "Activation Gate"),
                "frequency": _value(record, "Timing / Frequency", "Event Based"),
                "due_timeline": None,
                "responsible_person": _value(record, "Primary Duty Holder"),
                "non_compliance_consequence": None,
                "priority": "High",
                "origin": SEBI_ORIGIN,
                "active": "Yes",
                "remarks": _value(record, "Official Source URL"),
            }
            for record in source["compliance"]
            if (compliance_id := _value(record, "Production Compliance ID"))
        ],
        "audit_procedure_master": [
            {
                "audit_id": audit_id,
                "compliance_id": _value(record, "Production Compliance ID"),
                "audit_procedure": _value(record, "Audit Procedure"),
                "audit_method": _value(record, "Test Method"),
                "audit_frequency": _value(record, "Timing / Frequency", "Event Based"),
                "origin": SEBI_ORIGIN,
                "risk_focus": _value(record, "Control Objective"),
                "active": "Yes",
                "remarks": _value(record, "Official Source URL"),
            }
            for record in source["audits"]
            if (audit_id := _value(record, "Production Audit ID"))
        ],
        "evidence_master": [
            {
                "evidence_id": evidence_id,
                "audit_id": _value(record, "Production Audit ID"),
                "evidence_required": _value(record, "Evidence Required"),
                "evidence_type": _value(record, "Evidence Role"),
                "mandatory": "Yes",
                "retention_category": _value(record, "Retention / Preservation Basis"),
                "origin": SEBI_ORIGIN,
                "active": "Yes",
                "remarks": _value(record, "Official Source URL"),
            }
            for record in source["evidence"]
            if (evidence_id := _value(record, "Production Evidence ID"))
        ],
        "observation_master": [
            {
                "observation_id": observation_id,
                "audit_id": _value(record, "Production Audit ID"),
                "observation_template": _value(record, "Observation Statement Template"),
                "risk_level": _value(record, "Default Severity", "High"),
                "recommendation": _value(record, "Remediation Expectation"),
                "observation_category": _value(record, "Observation Category"),
                "origin": SEBI_ORIGIN,
                "active": "Yes",
                "remarks": _value(record, "Official Source URL"),
            }
            for record in source["observations"]
            if (observation_id := _value(record, "Production Observation ID"))
        ],
    }

    summary.rows_read = {
        "Law Master": len(source["laws"]),
        "Provision Master": len(source["provisions"]),
        "Compliance Requirement Master": len(source["compliance"]),
        "Audit Procedure Master": len(source["audits"]),
        "Evidence Master": len(source["evidence"]),
        "Observation Master": len(source["observations"]),
    }
    db = SessionLocal()
    try:
        if mode == "truncate":
            for table_name in reversed(TABLE_ORDER):
                db.execute(delete(tables[table_name]))
        for table_name in TABLE_ORDER:
            count = _upsert_rows(db, tables[table_name], records[table_name], mode)
            summary.rows_inserted[table_name] = count
            summary.rows_skipped[table_name] = 0

        # Audit items are snapshots. Refresh SEBI links after an import so
        # existing listed-company audits receive the official source too.
        law_master = tables["law_master"]
        db.execute(
            update(AuditEngagementItem)
            .where(
                AuditEngagementItem.dataset_key == SEBI_DATASET_KEY,
                AuditEngagementItem.law_id == law_master.c.law_id,
            )
            .values(official_source_url=law_master.c.official_source_url)
        )
        summary.status = "success"
        summary.completed_at = datetime.now(UTC)
        db.commit()
        return summary
    except Exception as error:
        db.rollback()
        summary.status = "failed"
        summary.errors.append(str(error))
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the SEBI Listed Entity overlay workbook.")
    parser.add_argument("workbook", help="Path to the frozen SEBI production workbook.")
    parser.add_argument("--mode", choices=["upsert", "truncate"], default="upsert")
    args = parser.parse_args()
    print(json.dumps(import_sebi_listed_overlay(args.workbook, args.mode).as_dict(), indent=2))


if __name__ == "__main__":
    main()
