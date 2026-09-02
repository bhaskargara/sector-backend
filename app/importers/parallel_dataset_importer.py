from __future__ import annotations

import argparse
import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.importers.pharmacy_dataset_importer import (
    DATASET_SHEETS,
    ImportSummary,
    PharmacyDatasetImporter,
)
from app.models.regulatory_v2 import iter_regulatory_tables

SHEET_NAME_BY_TABLE = {
    "sector_master": "Sector Master",
    "sub_sector_master": "Sub-Sector Master",
    "regulatory_authority_master": "Regulatory Authority Master",
    "compliance_area_master": "Compliance Area Master",
    "origin_master": "Origin Master",
    "enum_master": "Enum Master",
    "law_master": "Law Master",
    "law_compliance_area_map": "Law_ComplianceArea_Map",
    "applicability_matrix": "Applicability Matrix",
    "provision_master": "Provision Master",
    "provision_compliance_area_map": "Provision_ComplianceArea_Map",
    "compliance_requirement_master": "Compliance Requirement Master",
    "audit_procedure_master": "Audit Procedure Master",
    "evidence_master": "Evidence Master",
    "observation_master": "Observation Master",
}

SUPPORTED_DATASET_KEYS = {
    "bank",
    "common_core",
    "it",
    "manufacturing",
    "nbfc",
    "pharmacy",
}

# These are the only workbook tabs used for parallel regulatory datasets.
# Origin and enum records are generated internally from those records, keeping
# the workbook contract focused on the regulatory source data.
PARALLEL_IMPORT_ORDER = [
    "Sector Master",
    "Sub-Sector Master",
    "Regulatory Authority Master",
    "Compliance Area Master",
    "Law Master",
    "Law_ComplianceArea_Map",
    "Applicability Matrix",
    "Origin Master",
    "Enum Master",
    "Provision Master",
    "Provision_ComplianceArea_Map",
    "Compliance Requirement Master",
    "Audit Procedure Master",
    "Evidence Master",
    "Observation Master",
]


def build_dataset_sheet_config(dataset_key: str) -> dict[str, dict[str, Any]]:
    if dataset_key not in SUPPORTED_DATASET_KEYS:
        raise ValueError(
            f"Unsupported dataset_key '{dataset_key}'. Expected one of: "
            f"{', '.join(sorted(SUPPORTED_DATASET_KEYS))}"
        )

    tables_by_sheet = {
        SHEET_NAME_BY_TABLE[table.name]: table
        for table in iter_regulatory_tables(dataset_key)
    }
    missing = [
        sheet_name
        for sheet_name in PARALLEL_IMPORT_ORDER
        if sheet_name not in tables_by_sheet
    ]
    if missing:
        raise ValueError(
            f"Dataset '{dataset_key}' is missing table bindings for sheets: {', '.join(missing)}"
        )

    config: dict[str, dict[str, Any]] = {}
    for sheet_name, base_config in DATASET_SHEETS.items():
        if sheet_name not in tables_by_sheet:
            continue
        config[sheet_name] = {
            **base_config,
            "model": tables_by_sheet[sheet_name],
        }
    return config


class ParallelRegulatoryDatasetImporter(PharmacyDatasetImporter):
    def __init__(self, db: Session, dataset_key: str):
        self.dataset_key = dataset_key
        super().__init__(
            db,
            dataset_sheets=build_dataset_sheet_config(dataset_key),
            import_order=PARALLEL_IMPORT_ORDER,
            log_imports=False,
            # Older validated sector workbooks do not always include this
            # derived tab. Runtime scope is determined from Law/Provision data.
            optional_workbook_sheets={"Applicability Matrix"},
        )


def import_parallel_dataset(
    dataset_key: str,
    workbook_path: str,
    mode: str = "upsert",
) -> ImportSummary:
    db = SessionLocal()
    try:
        return ParallelRegulatoryDatasetImporter(
            db,
            dataset_key=dataset_key,
        ).import_workbook(workbook_path, mode=mode)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a regulatory workbook into a parallel dataset schema."
    )
    parser.add_argument(
        "dataset_key",
        choices=sorted(SUPPORTED_DATASET_KEYS),
        help="Target parallel dataset schema key.",
    )
    parser.add_argument("workbook", help="Path to the Excel workbook.")
    parser.add_argument("--mode", choices=["upsert", "truncate"], default="upsert")
    args = parser.parse_args()

    summary = import_parallel_dataset(
        dataset_key=args.dataset_key,
        workbook_path=args.workbook,
        mode=args.mode,
    )
    print(json.dumps(summary.as_dict(), indent=2))


if __name__ == "__main__":
    main()
