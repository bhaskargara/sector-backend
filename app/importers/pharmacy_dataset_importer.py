from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.sql.schema import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
# The generic parser is retained for the parallel importer only.  Concrete
# table bindings are injected by parallel_dataset_importer; it no longer loads
# the retired public regulatory ORM models.
(
    AuditProcedureMaster,
    ComplianceAreaMaster,
    ComplianceRequirementMaster,
    EnumMaster,
    EvidenceMaster,
    ImportLog,
    LawComplianceAreaMap,
    LawMaster,
    ObservationMaster,
    OriginMaster,
    ProvisionComplianceAreaMap,
    ProvisionMaster,
    RegulatoryAuthorityMaster,
    SectorMaster,
    SubSectorMaster,
) = (None,) * 15

DATASET_SHEETS: dict[str, dict[str, Any]] = {
    "Sector Master": {
        "model": SectorMaster,
        "pk": ["sector_id"],
        "columns": {
            "SectorID": "sector_id",
            "Sector Name": "sector_name",
            "Description": "description",
            "Active": "active",
            "Remark": "remark",
        },
        "optional_columns": ["Remark"],
    },
    "Sub-Sector Master": {
        "model": SubSectorMaster,
        "pk": ["sub_sector_id"],
        "columns": {
            "Sub-Sector ID": "sub_sector_id",
            "SectorID": "sector_id",
            "Sub-Sector Name": "sub_sector_name",
            "Description": "description",
            "Active": "active",
        },
        "fks": [("sector_id", "Sector Master", False)],
    },
    "Regulatory Authority Master": {
        "model": RegulatoryAuthorityMaster,
        "pk": ["authority_id"],
        "columns": {
            "Authority ID": "authority_id",
            "Regulatory Authority": "regulatory_authority",
            "Short Name": "short_name",
            "Authority Type": "authority_type",
            "Jurisdiction": "jurisdiction",
            "Parent Authority": "parent_authority",
            "Description": "description",
            "Active": "active",
        },
    },
    "Compliance Area Master": {
        "model": ComplianceAreaMaster,
        "pk": ["area_id"],
        "columns": {
            "Area ID": "area_id",
            "Parent Area ID": "parent_area_id",
            "Parent Area": "parent_area",
            "Compliance Area": "compliance_area",
            "Description": "description",
            "Display Order": "display_order",
            "Active": "active",
        },
        "fks": [("parent_area_id", "Compliance Area Master", True)],
    },
    "Law Master": {
        "model": LawMaster,
        "pk": ["law_id"],
        "columns": {
            "Law ID": "law_id",
            "Domain": "domain",
            "Sector": "sector",
            "Sub-Sector": "sub_sector",
            "Regulator": "regulator",
            "Authority Level": "authority_level",
            "Document Type": "document_type",
            "Parent Law": "parent_law",
            "Law Name": "law_name",
            "Law_ComplianceArea_Map": "law_compliance_area_map",
            "Applicability Type": "applicability_type",
            "Applicability Trigger": "applicability_trigger",
            "Active": "active",
            "Review Frequency": "review_frequency",
            "Remarks": "remarks",
        },
        "fks": [("parent_law", "Law Master", True)],
    },
    "Law_ComplianceArea_Map": {
        "model": LawComplianceAreaMap,
        "pk": ["map_id"],
        "columns": {
            "Map ID": "map_id",
            "Law ID": "law_id",
            "Compliance Area ID": "compliance_area_id",
            "Active Status": "active_status",
            "Remarks": "remarks",
        },
        "fks": [
            ("law_id", "Law Master", False),
            ("compliance_area_id", "Compliance Area Master", False),
        ],
    },
    "Applicability Matrix": {
        "model": None,
        "pk": ["sector", "sub_sector", "law_id"],
        "columns": {
            "Sector": "sector",
            "Sub-Sector": "sub_sector",
            "Law ID": "law_id",
            "Mandatory": "mandatory",
            "Conditional": "conditional",
            "Applicability Trigger": "applicability_trigger",
        },
        "fks": [("law_id", "Law Master", False)],
    },
    "Origin Master": {
        "model": OriginMaster,
        "pk": ["origin_code"],
        "columns": {
            "Origin Code": "origin_code",
            "Origin Name": "origin_name",
            "Description": "description",
        },
    },
    "Enum Master": {
        "model": EnumMaster,
        "pk": ["enum_type", "allowed_value"],
        "columns": {
            "Enum Type": "enum_type",
            "Allowed Value": "allowed_value",
            "Description": "description",
        },
    },
    "Provision Master": {
        "model": ProvisionMaster,
        "pk": ["provision_id"],
        "columns": {
            "Provision ID": "provision_id",
            "Law ID": "law_id",
            "Sub Sector ID": "sub_sector_id",
            "Provision Category": "provision_category",
            "Statutory Reference": "statutory_reference",
            "Provision Name": "provision_name",
            "Provision Description": "provision_description",
            "Origin": "origin",
            "Active": "active",
            "Remarks": "remarks",
        },
        "fks": [
            ("law_id", "Law Master", False),
            ("sub_sector_id", "Sub-Sector Master", True),
            ("origin", "Origin Master", False),
        ],
    },
    "Provision_ComplianceArea_Map": {
        "model": ProvisionComplianceAreaMap,
        "pk": ["map_id"],
        "columns": {
            "Map ID": "map_id",
            "Provision ID": "provision_id",
            "Compliance Area ID": "compliance_area_id",
            "Active": "active",
            "Remarks": "remarks",
        },
        "fks": [
            ("provision_id", "Provision Master", False),
            ("compliance_area_id", "Compliance Area Master", False),
        ],
    },
    "Compliance Requirement Master": {
        "model": ComplianceRequirementMaster,
        "pk": ["compliance_id"],
        "columns": {
            "Compliance ID": "compliance_id",
            "Provision ID": "provision_id",
            "Compliance Area ID": "compliance_area_id",
            "Compliance Requirement": "compliance_requirement",
            "Compliance Objective": "compliance_objective",
            "Applicability": "applicability",
            "Frequency": "frequency",
            "Due Timeline": "due_timeline",
            "Responsible Person": "responsible_person",
            "Non-Compliance Consequence": "non_compliance_consequence",
            "Priority": "priority",
            "Origin": "origin",
            "Active": "active",
            "Remarks": "remarks",
        },
        "fks": [
            ("provision_id", "Provision Master", False),
            ("compliance_area_id", "Compliance Area Master", False),
            ("origin", "Origin Master", False),
        ],
    },
    "Audit Procedure Master": {
        "model": AuditProcedureMaster,
        "pk": ["audit_id"],
        "columns": {
            "Audit ID": "audit_id",
            "Compliance ID": "compliance_id",
            "Audit Procedure": "audit_procedure",
            "Audit Method": "audit_method",
            "Audit Frequency": "audit_frequency",
            "Origin": "origin",
            "Risk Focus": "risk_focus",
            "Active": "active",
            "Remarks": "remarks",
        },
        "fks": [
            ("compliance_id", "Compliance Requirement Master", False),
            ("origin", "Origin Master", False),
        ],
    },
    "Evidence Master": {
        "model": EvidenceMaster,
        "pk": ["evidence_id"],
        "columns": {
            "Evidence ID": "evidence_id",
            "Audit ID": "audit_id",
            "Evidence Required": "evidence_required",
            "Evidence Type": "evidence_type",
            "Mandatory": "mandatory",
            "Retention Category": "retention_category",
            "Origin": "origin",
            "Active": "active",
            "Remarks": "remarks",
        },
        "fks": [
            ("audit_id", "Audit Procedure Master", False),
            ("origin", "Origin Master", False),
        ],
    },
    "Observation Master": {
        "model": ObservationMaster,
        "pk": ["observation_id"],
        "columns": {
            "Observation ID": "observation_id",
            "Audit ID": "audit_id",
            "Observation Template": "observation_template",
            "Risk Level": "risk_level",
            "Recommendation": "recommendation",
            "Observation Category": "observation_category",
            "Origin": "origin",
            "Active": "active",
            "Remarks": "remarks",
        },
        "fks": [
            ("audit_id", "Audit Procedure Master", False),
            ("origin", "Origin Master", False),
        ],
    },
}

SHEET_ALIASES = {
    "Regulatory Authority Master": ["Regulatory Master"],
}

PLACEHOLDER_LAW_MATCHERS = {
    "REUSE_EXISTING_CONSUMER_PROTECTION_LAW_ID": [
        "Consumer Protection Act, 2019",
    ],
    "REUSE_EXISTING_CONSUMER_PROTECTION_ECOMMERCE_LAW_ID": [
        "Consumer Protection (E-Commerce) Rules, 2020",
    ],
    "REUSE_EXISTING_DPDP_LAW_ID": [
        "Digital Personal Data Protection Act, 2023",
    ],
    "REUSE_EXISTING_INTERMEDIARY_RULES_LAW_ID": [
        "Intermediary Guidelines and Digital Media Ethics Code",
    ],
}

IMPORT_ORDER = [
    "Sector Master",
    "Sub-Sector Master",
    "Regulatory Authority Master",
    "Compliance Area Master",
    "Law Master",
    "Law_ComplianceArea_Map",
    "Origin Master",
    "Enum Master",
    "Provision Master",
    "Provision_ComplianceArea_Map",
    "Compliance Requirement Master",
    "Audit Procedure Master",
    "Evidence Master",
    "Observation Master",
]

CONTROLLED_COLUMNS = {
    ("Sector Master", "active"): "Active",
    ("Sub-Sector Master", "active"): "Active",
    ("Regulatory Authority Master", "active"): "Active",
    ("Compliance Area Master", "active"): "Active",
    ("Law Master", "active"): "Active",
    ("Law_ComplianceArea_Map", "active_status"): "Active",
    ("Provision Master", "provision_category"): "Provision Category",
    ("Provision Master", "active"): "Active",
    ("Provision_ComplianceArea_Map", "active"): "Active",
    ("Compliance Requirement Master", "priority"): "Priority",
    ("Compliance Requirement Master", "active"): "Active",
    ("Audit Procedure Master", "audit_method"): "Audit Method",
    ("Audit Procedure Master", "audit_frequency"): "Audit Frequency",
    ("Audit Procedure Master", "active"): "Active",
    ("Evidence Master", "evidence_type"): "Evidence Type",
    ("Evidence Master", "mandatory"): "Mandatory",
    ("Evidence Master", "retention_category"): "Retention Category",
    ("Evidence Master", "active"): "Active",
    ("Observation Master", "risk_level"): "Risk Level",
    ("Observation Master", "observation_category"): "Observation Category",
    ("Observation Master", "active"): "Active",
}

NULL_MARKERS = {"", "-", "nan", "none", "null", "n/a", "na"}


@dataclass
class ImportSummary:
    workbook_path: str
    mode: str
    status: str = "success"
    rows_read: dict[str, int] = field(default_factory=dict)
    rows_inserted: dict[str, int] = field(default_factory=dict)
    rows_skipped: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    completed_at: datetime | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "workbook_path": self.workbook_path,
            "mode": self.mode,
            "status": self.status,
            "rows_read": self.rows_read,
            "rows_inserted": self.rows_inserted,
            "rows_skipped": self.rows_skipped,
            "errors": self.errors,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }


class PharmacyDatasetImporter:
    def __init__(
        self,
        db: Session,
        dataset_sheets: dict[str, dict[str, Any]] | None = None,
        import_order: list[str] | None = None,
        log_imports: bool = True,
        optional_workbook_sheets: set[str] | None = None,
    ):
        self.db = db
        self.dataset_sheets = dataset_sheets or DATASET_SHEETS
        self.import_order = import_order or IMPORT_ORDER
        self.log_imports = log_imports
        self.optional_workbook_sheets = optional_workbook_sheets or set()

    def import_workbook(self, workbook_path: str, mode: str = "upsert") -> ImportSummary:
        path = Path(workbook_path)
        if mode not in {"upsert", "truncate"}:
            raise ValueError("mode must be 'upsert' or 'truncate'")

        summary = ImportSummary(workbook_path=str(path), mode=mode)
        datasets: dict[str, list[dict[str, Any]]] = {}
        try:
            workbook_sheets = pd.ExcelFile(path, engine="openpyxl").sheet_names
            sheet_lookup = self._build_sheet_lookup(workbook_sheets)
            self._validate_sheets(sheet_lookup)
            for sheet_name in self.import_order:
                if sheet_name in {"Origin Master", "Enum Master"} and sheet_name not in sheet_lookup:
                    continue
                if (
                    sheet_name in self.optional_workbook_sheets
                    and sheet_name not in sheet_lookup
                ):
                    datasets[sheet_name] = []
                    summary.rows_read[sheet_name] = 0
                    continue
                records = self._read_sheet(path, sheet_name, sheet_lookup[sheet_name])
                datasets[sheet_name] = records
                summary.rows_read[sheet_name] = len(records)
                self._validate_duplicate_keys(sheet_name, records)
            # Parallel datasets isolate each sector in its own PostgreSQL schema,
            # so workbook IDs must remain untouched.  This also keeps IDs stable
            # for traceability back to the published sector workbook.
            # Frozen workbooks can include an Origin Master which predates
            # later validation records. Merge every origin referenced by the
            # actual import rows, rather than rejecting those valid rows.
            generated_origins = self._build_origin_master_records(datasets)
            if "Origin Master" not in datasets:
                datasets["Origin Master"] = generated_origins
            else:
                existing_origin_codes = {
                    record["origin_code"]
                    for record in datasets["Origin Master"]
                    if record.get("origin_code")
                }
                datasets["Origin Master"].extend(
                    record
                    for record in generated_origins
                    if record["origin_code"] not in existing_origin_codes
                )
            summary.rows_read["Origin Master"] = len(datasets["Origin Master"])
            self._validate_duplicate_keys("Origin Master", datasets["Origin Master"])
            # Keep the frozen Enum Master as the source of descriptions, while
            # adding values which are present in the current regulatory rows.
            generated_enums = self._build_enum_master_records(datasets)
            if "Enum Master" not in datasets:
                datasets["Enum Master"] = generated_enums
            else:
                existing_enum_keys = {
                    (record["enum_type"], record["allowed_value"])
                    for record in datasets["Enum Master"]
                    if record.get("enum_type") and record.get("allowed_value")
                }
                datasets["Enum Master"].extend(
                    record
                    for record in generated_enums
                    if (record["enum_type"], record["allowed_value"])
                    not in existing_enum_keys
                )
            summary.rows_read["Enum Master"] = len(datasets["Enum Master"])
            self._validate_duplicate_keys("Enum Master", datasets["Enum Master"])
            self._resolve_placeholder_law_ids(datasets)
            self._materialize_delta_laws_from_provisions(datasets)
            self._normalize_sub_sector_references(datasets)
            self._materialize_missing_sub_sectors(datasets)
            self._normalize_compliance_area_hierarchy(datasets)
            self._normalize_parent_law_references(datasets)
            self._normalize_required_law_fields(datasets)
            self._prune_incomplete_relationship_chains(datasets)
            self._normalize_audit_references(datasets)
            self._backfill_law_scope_from_provisions(datasets)
            self._validate_foreign_keys(datasets)
            self._validate_enum_values(datasets)
            if mode == "truncate":
                self._truncate_tables()
            for sheet_name in self.import_order:
                inserted = self._persist_sheet(sheet_name, datasets[sheet_name], mode)
                summary.rows_inserted[sheet_name] = inserted
                summary.rows_skipped[sheet_name] = max(
                    summary.rows_read[sheet_name] - inserted,
                    0,
                )
            summary.completed_at = datetime.utcnow()
            self._store_log(summary)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            summary.status = "failed"
            summary.errors.append(str(exc))
            summary.completed_at = datetime.utcnow()
            self._store_failed_log(summary)
            raise
        return summary

    def _build_sheet_lookup(self, workbook_sheets: list[str]) -> dict[str, str]:
        sheet_lookup: dict[str, str] = {}
        for sheet_name in self.import_order:
            if sheet_name in workbook_sheets:
                sheet_lookup[sheet_name] = sheet_name
                continue
            for alias in SHEET_ALIASES.get(sheet_name, []):
                if alias in workbook_sheets:
                    sheet_lookup[sheet_name] = alias
                    break
        return sheet_lookup

    def _validate_sheets(self, sheet_lookup: dict[str, str]) -> None:
        missing = [
            sheet
            for sheet in self.import_order
            if sheet not in sheet_lookup
            and sheet not in {"Origin Master", "Enum Master"}
            and sheet not in self.optional_workbook_sheets
        ]
        if missing:
            raise ValueError(f"Missing required sheets: {', '.join(missing)}")

    def _read_sheet(self, path: Path, sheet_name: str, actual_sheet_name: str) -> list[dict[str, Any]]:
        if sheet_name == "Law Master":
            return self._read_law_sheet(path, actual_sheet_name)
        if sheet_name == "Provision Master":
            return self._read_provision_sheet(path, actual_sheet_name)
        if sheet_name == "Provision_ComplianceArea_Map":
            return self._read_provision_compliance_area_map_sheet(path, actual_sheet_name)
        if sheet_name == "Compliance Requirement Master":
            return self._read_compliance_requirement_sheet(path, actual_sheet_name)
        if sheet_name == "Audit Procedure Master":
            return self._read_audit_procedure_sheet(path, actual_sheet_name)
        if sheet_name == "Evidence Master":
            return self._read_evidence_sheet(path, actual_sheet_name)
        if sheet_name == "Observation Master":
            return self._read_observation_sheet(path, actual_sheet_name)

        df = pd.read_excel(path, sheet_name=actual_sheet_name, engine="openpyxl", dtype=object)
        return self._read_sheet_standard(df, sheet_name)

    def _read_law_sheet(self, path: Path, actual_sheet_name: str) -> list[dict[str, Any]]:
        df = pd.read_excel(path, sheet_name=actual_sheet_name, engine="openpyxl", dtype=object)
        extended_law_columns = {
            "Domain ID",
            "Sector ID",
            "Regulatory Authority ID",
            "Law Title",
        }
        if not extended_law_columns.intersection(df.columns):
            return self._read_sheet_standard(df, "Law Master")

        sector_lookup = self._load_lookup(path, "Sector Master", "SectorID", "Sector Name")
        default_sector_name = next(iter(sector_lookup.values()), None)
        domain_lookup = self._load_optional_lookup(path, "Domain Master", "Domain ID", "Domain Name")
        sub_sector_lookup = self._load_lookup(
            path,
            "Sub-Sector Master",
            "Sub-Sector ID",
            "Sub-Sector Name",
        )
        regulator_lookup = self._load_optional_lookup(
            path,
            "Regulatory Authority Master",
            "Authority ID",
            "Short Name",
            fallback_column="Regulatory Authority",
        )

        records = []
        for record in df.to_dict(orient="records"):
            remarks = self._clean_value(record.get("Remarks"))
            normalized = {
                "law_id": self._clean_value(record.get("Law ID")),
                "domain": self._resolve_lookup_value(
                    self._clean_value(record.get("Domain")),
                    self._clean_value(record.get("Domain ID")),
                    domain_lookup,
                ),
                "sector": self._resolve_lookup_value(
                    self._clean_value(record.get("Sector")),
                    self._clean_value(record.get("Sector ID")),
                    sector_lookup,
                    default_value=default_sector_name,
                ),
                "sub_sector": self._derive_law_sub_sector(
                    self._clean_value(record.get("Sub-Sector")),
                    remarks,
                    sub_sector_lookup,
                ),
                "regulator": self._resolve_lookup_value(
                    self._clean_value(record.get("Regulator")),
                    self._clean_value(record.get("Regulatory Authority ID")),
                    regulator_lookup,
                    default_value=self._clean_value(record.get("Regulatory Authority ID")),
                ),
                "authority_level": self._clean_value(record.get("Authority Level")),
                "document_type": self._clean_value(record.get("Document Type")),
                "parent_law": self._clean_value(record.get("Parent Law")),
                "law_name": self._clean_value(record.get("Law Name"))
                or self._clean_value(record.get("Law Title")),
                "law_compliance_area_map": self._clean_value(record.get("Law_ComplianceArea_Map"))
                or self._clean_value(record.get("Map ID")),
                "applicability_type": self._clean_value(record.get("Applicability Type"))
                or self._clean_value(record.get("Applicability")),
                "applicability_trigger": self._clean_value(record.get("Applicability Trigger"))
                or self._clean_value(record.get("Applicability Description")),
                "active": self._clean_value(record.get("Active")) or "Yes",
                "review_frequency": self._clean_value(record.get("Review Frequency")),
                "remarks": remarks,
            }
            if self._has_payload(normalized):
                records.append(normalized)
        return self._merge_duplicate_law_records(records)

    def _read_provision_sheet(self, path: Path, actual_sheet_name: str) -> list[dict[str, Any]]:
        df = pd.read_excel(path, sheet_name=actual_sheet_name, engine="openpyxl", dtype=object)
        if "Section / Rule" not in df.columns:
            return self._read_sheet_standard(df, "Provision Master")

        records = []
        for record in df.to_dict(orient="records"):
            normalized = {
                "provision_id": self._clean_value(record.get("Provision ID")),
                "law_id": self._clean_value(record.get("Law ID")),
                "sub_sector_id": self._derive_sub_sector_id(record),
                "provision_category": self._clean_value(record.get("Provision Type")),
                "statutory_reference": self._clean_value(record.get("Section / Rule")),
                "provision_name": self._clean_value(record.get("Provision Name")),
                "provision_description": self._clean_value(record.get("Provision Description")),
                "origin": self._derive_origin(record),
                "active": self._clean_value(record.get("Active")) or "Yes",
                "remarks": self._clean_value(record.get("Remarks")),
            }
            if self._has_payload(normalized):
                records.append(normalized)
        return records

    def _read_provision_compliance_area_map_sheet(
        self,
        path: Path,
        actual_sheet_name: str,
    ) -> list[dict[str, Any]]:
        df = pd.read_excel(path, sheet_name=actual_sheet_name, engine="openpyxl", dtype=object)
        if "Active Status" not in df.columns:
            return self._read_sheet_standard(df, "Provision_ComplianceArea_Map")

        records = []
        for record in df.to_dict(orient="records"):
            normalized = {
                "map_id": self._clean_value(record.get("Map ID")),
                "provision_id": self._clean_value(record.get("Provision ID")),
                "compliance_area_id": self._clean_value(record.get("Compliance Area ID")),
                "active": self._clean_value(record.get("Active Status")) or "Yes",
                "remarks": self._clean_value(record.get("Remarks")),
            }
            if self._has_payload(normalized):
                records.append(normalized)
        return records

    def _read_compliance_requirement_sheet(
        self,
        path: Path,
        actual_sheet_name: str,
    ) -> list[dict[str, Any]]:
        df = pd.read_excel(path, sheet_name=actual_sheet_name, engine="openpyxl", dtype=object)
        if "Source Type" not in df.columns:
            return self._read_sheet_standard(df, "Compliance Requirement Master")

        records = []
        for record in df.to_dict(orient="records"):
            normalized = {
                "compliance_id": self._clean_value(record.get("Compliance ID")),
                "provision_id": self._clean_value(record.get("Provision ID")),
                "compliance_area_id": self._clean_value(record.get("Compliance Area ID")),
                "compliance_requirement": self._clean_value(record.get("Compliance Requirement")),
                "compliance_objective": self._clean_value(record.get("Compliance Objective")),
                "applicability": self._clean_value(record.get("Applicability")),
                "frequency": self._clean_value(record.get("Frequency")),
                "due_timeline": self._clean_value(record.get("Due Timeline")),
                "responsible_person": self._clean_value(record.get("Responsible Person")),
                "non_compliance_consequence": self._clean_value(record.get("Non-Compliance Consequence")),
                "priority": self._clean_value(record.get("Priority")),
                "origin": self._derive_origin(record),
                "active": self._clean_value(record.get("Active")) or "Yes",
                "remarks": self._clean_value(record.get("Remarks")),
            }
            if self._has_payload(normalized):
                records.append(normalized)
        return records

    def _read_audit_procedure_sheet(
        self,
        path: Path,
        actual_sheet_name: str,
    ) -> list[dict[str, Any]]:
        df = pd.read_excel(path, sheet_name=actual_sheet_name, engine="openpyxl", dtype=object)
        if "Audit Procedure ID" not in df.columns:
            return self._read_sheet_standard(df, "Audit Procedure Master")

        records = []
        for record in df.to_dict(orient="records"):
            normalized = {
                "audit_id": self._clean_value(record.get("Audit Procedure ID")),
                "compliance_id": self._clean_value(record.get("Compliance ID")),
                "audit_procedure": self._clean_value(record.get("Audit Procedure")),
                "audit_method": self._clean_value(record.get("Verification Method")),
                "audit_frequency": self._clean_value(record.get("Frequency")),
                "origin": self._derive_origin(record),
                "risk_focus": self._clean_value(record.get("Risk Rating")),
                "active": "Yes",
                "remarks": self._clean_value(record.get("Remarks")),
            }
            if self._has_payload(normalized):
                records.append(normalized)
        return records

    def _read_evidence_sheet(self, path: Path, actual_sheet_name: str) -> list[dict[str, Any]]:
        df = pd.read_excel(path, sheet_name=actual_sheet_name, engine="openpyxl", dtype=object)
        if "Audit Procedure ID" not in df.columns:
            return self._read_sheet_standard(df, "Evidence Master")

        records = []
        for record in df.to_dict(orient="records"):
            normalized = {
                "evidence_id": self._clean_value(record.get("Evidence ID")),
                "audit_id": self._clean_value(record.get("Audit Procedure ID"))
                or self._clean_value(record.get("Compliance ID")),
                "evidence_required": self._clean_value(record.get("Evidence Required"))
                or self._clean_value(record.get("Evidence Type"))
                or "Primary evidence",
                "evidence_type": self._clean_value(record.get("Evidence Type")),
                "mandatory": self._clean_value(record.get("Mandatory")) or "Yes",
                "retention_category": self._clean_value(record.get("Retention Period")),
                "origin": self._derive_origin(record),
                "active": "Yes",
                "remarks": self._clean_value(record.get("Remark")),
            }
            if self._has_payload(normalized):
                records.append(normalized)
        return records

    def _read_observation_sheet(self, path: Path, actual_sheet_name: str) -> list[dict[str, Any]]:
        df = pd.read_excel(path, sheet_name=actual_sheet_name, engine="openpyxl", dtype=object)
        if "Audit Procedure ID" not in df.columns:
            return self._read_sheet_standard(df, "Observation Master")

        records = []
        for record in df.to_dict(orient="records"):
            normalized = {
                "observation_id": self._clean_value(record.get("Observation ID")),
                "audit_id": self._clean_value(record.get("Audit Procedure ID"))
                or self._clean_value(record.get("Compliance ID")),
                "observation_template": self._clean_value(record.get("Observation Template"))
                or self._clean_value(record.get("Recommendation"))
                or "Observation requires review.",
                "risk_level": self._clean_value(record.get("Risk Level")) or "Medium",
                "recommendation": self._clean_value(record.get("Recommendation")),
                "observation_category": None,
                "origin": self._derive_origin(record),
                "active": self._clean_value(record.get("Active")) or "Yes",
                "remarks": self._clean_value(record.get("Remarks")),
            }
            if self._has_payload(normalized):
                records.append(normalized)
        return records

    def _read_sheet_standard(self, df: pd.DataFrame, sheet_name: str) -> list[dict[str, Any]]:
        config = self.dataset_sheets[sheet_name]
        optional_columns = set(config.get("optional_columns", []))
        missing_columns = [
            column
            for column in config["columns"]
            if column not in df.columns and column not in optional_columns
        ]
        if missing_columns:
            raise ValueError(
                f"{sheet_name} missing required columns: {', '.join(missing_columns)}"
            )
        for column in optional_columns:
            if column not in df.columns:
                df[column] = None
        df = df[list(config["columns"].keys())].rename(columns=config["columns"])
        records = []
        for record in df.to_dict(orient="records"):
            normalized = {
                key: self._clean_value(value)
                for key, value in record.items()
            }
            if not self._has_payload(normalized):
                continue
            # Some frozen workbooks retain blank quarantine/QA rows.  They are
            # not master-data records and cannot be imported without a key.
            if any(normalized.get(column) is None for column in config["pk"]):
                continue
            if "active" in normalized and normalized["active"] is None:
                normalized["active"] = "Yes"
            if "active_status" in normalized and normalized["active_status"] is None:
                normalized["active_status"] = "Yes"
            records.append(normalized)
        return records

    def _build_origin_master_records(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        origins: dict[str, str] = {}
        for sheet_name in [
            "Provision Master",
            "Compliance Requirement Master",
            "Audit Procedure Master",
            "Evidence Master",
            "Observation Master",
        ]:
            for record in datasets.get(sheet_name, []):
                origin = record.get("origin")
                if origin is None:
                    continue
                origins.setdefault(origin, origin)
        return [
            {
                "origin_code": origin_code,
                "origin_name": origin_name,
                "description": None,
            }
            for origin_code, origin_name in sorted(origins.items())
        ]

    def _build_enum_master_records(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        enum_entries: set[tuple[str, str]] = set()
        for (sheet_name, column), enum_type in CONTROLLED_COLUMNS.items():
            values = sorted(
                {
                    record[column]
                    for record in datasets.get(sheet_name, [])
                    if record.get(column) is not None
                }
            )
            for value in values:
                enum_entries.add((enum_type, value))
        return [
            {
                "enum_type": enum_type,
                "allowed_value": allowed_value,
                "description": None,
            }
            for enum_type, allowed_value in sorted(enum_entries)
        ]

    def _derive_origin(self, record: dict[str, Any]) -> str:
        source_type = self._clean_value(record.get("Source Type"))
        if isinstance(source_type, str) and source_type.strip().lower() == "core":
            return "CORE"

        origin_name = self._clean_value(record.get("Origin Sub-Sector Name"))
        origin_sub_sector_id = self._clean_value(record.get("Origin Sub-Sector ID"))
        return origin_name or origin_sub_sector_id or source_type or "CORE"

    def _derive_sub_sector_id(self, record: dict[str, Any]) -> str | None:
        source_type = self._clean_value(record.get("Source Type"))
        if isinstance(source_type, str) and source_type.strip().lower() == "core":
            return None
        origin_sub_sector_id = self._clean_value(record.get("Origin Sub-Sector ID"))
        if (
            isinstance(origin_sub_sector_id, str)
            and re.search(r"(?:^|[-_])core$", origin_sub_sector_id, re.IGNORECASE)
        ):
            return None
        return origin_sub_sector_id

    def _derive_law_sub_sector(
        self,
        raw_sub_sector: str | None,
        remarks: str | None,
        sub_sector_lookup: dict[str, str],
    ) -> str | None:
        if raw_sub_sector in {None, "All"}:
            if raw_sub_sector == "All":
                return "All"
            sub_sector_id = self._extract_sub_sector_id(remarks)
            # An empty sub-sector on a law means it applies at sector level.
            # When remarks carry a SUBnnn delta reference, retain that more
            # precise scope; otherwise represent the sector-wide scope as All.
            return sub_sector_lookup.get(sub_sector_id, "All")
        if raw_sub_sector in sub_sector_lookup:
            return sub_sector_lookup[raw_sub_sector]
        return raw_sub_sector

    @staticmethod
    def _extract_sub_sector_id(text: str | None) -> str | None:
        if not text:
            return None
        match = re.search(r"\bSUB\d{3}\b", text)
        return match.group(0) if match else None

    @staticmethod
    def _load_lookup(
        path: Path,
        sheet_name: str,
        key_column: str,
        value_column: str,
        fallback_column: str | None = None,
    ) -> dict[str, str]:
        df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl", dtype=object)
        lookup: dict[str, str] = {}
        for record in df.to_dict(orient="records"):
            key = PharmacyDatasetImporter._clean_value(record.get(key_column))
            value = PharmacyDatasetImporter._clean_value(record.get(value_column))
            if value is None and fallback_column:
                value = PharmacyDatasetImporter._clean_value(record.get(fallback_column))
            if key and value:
                lookup[key] = value
        return lookup

    @staticmethod
    def _load_optional_lookup(
        path: Path,
        sheet_name: str,
        key_column: str,
        value_column: str,
        fallback_column: str | None = None,
    ) -> dict[str, str]:
        workbook_sheets = pd.ExcelFile(path, engine="openpyxl").sheet_names
        actual_sheet_name = sheet_name
        if actual_sheet_name not in workbook_sheets:
            actual_sheet_name = next(
                (alias for alias in SHEET_ALIASES.get(sheet_name, []) if alias in workbook_sheets),
                sheet_name,
            )
        if actual_sheet_name not in workbook_sheets:
            return {}
        return PharmacyDatasetImporter._load_lookup(
            path,
            actual_sheet_name,
            key_column,
            value_column,
            fallback_column=fallback_column,
        )

    @staticmethod
    def _resolve_lookup_value(
        raw_value: str | None,
        fallback_id: str | None,
        lookup: dict[str, str],
        default_value: str | None = None,
    ) -> str | None:
        if raw_value in lookup:
            return lookup[raw_value]
        if fallback_id in lookup:
            return lookup[fallback_id]
        unresolved_value = raw_value or fallback_id
        if unresolved_value and re.fullmatch(r"[A-Z]{2,}\d+", unresolved_value):
            return default_value or unresolved_value
        return raw_value or fallback_id or default_value

    @staticmethod
    def _is_modern_sector_dataset(workbook_sheets: list[str]) -> bool:
        return "Domain Master" in workbook_sheets

    def _derive_dataset_prefix(self, datasets: dict[str, list[dict[str, Any]]]) -> str:
        sector_name = (
            datasets.get("Sector Master", [{}])[0].get("sector_name")
            if datasets.get("Sector Master")
            else None
        )
        if not sector_name:
            return "DATA"
        tokens = re.findall(r"[A-Za-z0-9]+", sector_name)
        if "Information" in tokens and "Technology" in tokens:
            return "IT"
        return "".join(token[0].upper() for token in tokens[:3]) or "DATA"

    def _apply_dataset_prefix(self, datasets: dict[str, list[dict[str, Any]]], prefix: str) -> None:
        field_map = {
            "Sector Master": ["sector_id"],
            "Sub-Sector Master": ["sub_sector_id", "sector_id"],
            "Regulatory Authority Master": ["authority_id", "parent_authority"],
            "Compliance Area Master": ["area_id", "parent_area_id"],
            "Law Master": ["law_id", "parent_law", "law_compliance_area_map"],
            "Law_ComplianceArea_Map": ["map_id", "law_id", "compliance_area_id"],
            "Provision Master": ["provision_id", "law_id", "sub_sector_id"],
            "Provision_ComplianceArea_Map": ["map_id", "provision_id", "compliance_area_id"],
            "Compliance Requirement Master": ["compliance_id", "provision_id", "compliance_area_id"],
            "Audit Procedure Master": ["audit_id", "compliance_id"],
            "Evidence Master": ["evidence_id", "audit_id"],
            "Observation Master": ["observation_id", "audit_id"],
        }
        for sheet_name, fields in field_map.items():
            for record in datasets.get(sheet_name, []):
                for field in fields:
                    value = record.get(field)
                    if value is None:
                        continue
                    record[field] = self._prefix_identifier(prefix, value)

    @staticmethod
    def _prefix_identifier(prefix: str, value: str) -> str:
        cleaned = PharmacyDatasetImporter._clean_value(value)
        if cleaned is None:
            return value
        if cleaned.startswith("REUSE_EXISTING_"):
            return cleaned
        if cleaned.startswith(f"{prefix}-"):
            return cleaned
        return f"{prefix}-{cleaned}"

    def _resolve_placeholder_law_ids(self, datasets: dict[str, list[dict[str, Any]]]) -> None:
        laws = datasets.get("Law Master", [])
        if not laws:
            return

        resolved_ids: dict[str, str] = {}
        for placeholder, matchers in PLACEHOLDER_LAW_MATCHERS.items():
            matched_law = next(
                (
                    law
                    for law in laws
                    if any(
                        matcher.lower() in str(law.get("law_name") or "").lower()
                        for matcher in matchers
                    )
                ),
                None,
            )
            if matched_law:
                resolved_ids[placeholder] = matched_law["law_id"]

        for record in datasets.get("Provision Master", []):
            law_id = record.get("law_id")
            if law_id in resolved_ids:
                record["law_id"] = resolved_ids[law_id]

    def _backfill_law_scope_from_provisions(self, datasets: dict[str, list[dict[str, Any]]]) -> None:
        laws = datasets.get("Law Master", [])
        if not laws:
            return

        default_sector_name = (
            datasets.get("Sector Master", [{}])[0].get("sector_name")
            if datasets.get("Sector Master")
            else None
        )
        sub_sector_lookup = {
            record["sub_sector_id"]: record["sub_sector_name"]
            for record in datasets.get("Sub-Sector Master", [])
            if record.get("sub_sector_id") and record.get("sub_sector_name")
        }
        provision_sub_sectors: dict[str, set[str]] = {}
        for provision in datasets.get("Provision Master", []):
            law_id = provision.get("law_id")
            sub_sector_id = provision.get("sub_sector_id")
            if not law_id or not sub_sector_id:
                continue
            provision_sub_sectors.setdefault(law_id, set()).add(sub_sector_id)

        for law in laws:
            if not law.get("sector"):
                law["sector"] = default_sector_name
            if law.get("sub_sector"):
                continue
            matched_sub_sectors = provision_sub_sectors.get(law.get("law_id"), set())
            if len(matched_sub_sectors) == 1:
                only_sub_sector_id = next(iter(matched_sub_sectors))
                law["sub_sector"] = sub_sector_lookup.get(only_sub_sector_id, only_sub_sector_id)
            elif len(matched_sub_sectors) > 1:
                law["sub_sector"] = "All"

    def _normalize_compliance_area_hierarchy(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> None:
        compliance_areas = datasets.get("Compliance Area Master", [])
        if not compliance_areas:
            return
        valid_area_ids = {
            record["area_id"]
            for record in compliance_areas
            if record.get("area_id") is not None
        }
        for record in compliance_areas:
            parent_area_id = record.get("parent_area_id")
            if parent_area_id and parent_area_id not in valid_area_ids:
                record["parent_area_id"] = None

    def _normalize_sub_sector_references(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> None:
        for record in datasets.get("Provision Master", []):
            sub_sector_id = record.get("sub_sector_id")
            if isinstance(sub_sector_id, str) and sub_sector_id.strip().casefold() == "all":
                # Workbooks use "All" to mean sector-wide. The database uses
                # NULL so it is not mistaken for a sub-sector foreign key.
                record["sub_sector_id"] = None

        sub_sectors = datasets.get("Sub-Sector Master", [])
        if not sub_sectors:
            return
        valid_sub_sector_ids = {
            record["sub_sector_id"]
            for record in sub_sectors
            if record.get("sub_sector_id")
        }
        alias_map: dict[str, str] = {}
        short_id_candidates: dict[str, set[str]] = {}
        for sub_sector_id in valid_sub_sector_ids:
            alias_map[sub_sector_id] = sub_sector_id
            match = re.fullmatch(r"([A-Z0-9]+)-[A-Z]+SUB(\d+)", sub_sector_id)
            if match:
                alias_map[f"{match.group(1)}-SUB{match.group(2)}"] = sub_sector_id
            suffix_match = re.search(r"SUB(\d+)$", sub_sector_id)
            if suffix_match:
                short_id_candidates.setdefault(
                    f"SUB{suffix_match.group(1)}",
                    set(),
                ).add(sub_sector_id)

        # Some sector workbooks use BANKSUB001 in the master but SUB001 in
        # delta rows. Resolve the short form only when it maps unambiguously.
        for short_id, candidates in short_id_candidates.items():
            if len(candidates) == 1:
                alias_map[short_id] = next(iter(candidates))

        for record in datasets.get("Provision Master", []):
            sub_sector_id = record.get("sub_sector_id")
            if sub_sector_id is None:
                continue
            record["sub_sector_id"] = alias_map.get(sub_sector_id, sub_sector_id)

    def _materialize_missing_sub_sectors(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> None:
        sub_sectors = datasets.get("Sub-Sector Master", [])
        if not sub_sectors:
            return
        valid_sub_sector_ids = {
            record["sub_sector_id"]
            for record in sub_sectors
            if record.get("sub_sector_id")
        }
        sector_ids_by_prefix = {
            sector_record["sector_id"].split("-", 1)[0]: sector_record["sector_id"]
            for sector_record in datasets.get("Sector Master", [])
            if sector_record.get("sector_id")
        }
        missing_sub_sectors: dict[str, str] = {}
        for record in datasets.get("Provision Master", []):
            sub_sector_id = record.get("sub_sector_id")
            if sub_sector_id is None or sub_sector_id in valid_sub_sector_ids:
                continue
            missing_sub_sectors.setdefault(
                sub_sector_id,
                record.get("origin")
                or sub_sector_id,
            )
        for sub_sector_id, sub_sector_name in missing_sub_sectors.items():
            prefix = sub_sector_id.split("-", 1)[0]
            sector_id = sector_ids_by_prefix.get(prefix)
            if sector_id is None:
                continue
            sub_sectors.append(
                {
                    "sub_sector_id": sub_sector_id,
                    "sector_id": sector_id,
                    "sub_sector_name": sub_sector_name,
                    "description": "Importer-generated from referenced provision rows.",
                    "active": "Yes",
                }
            )
            valid_sub_sector_ids.add(sub_sector_id)

    def _materialize_delta_laws_from_provisions(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> None:
        provisions = datasets.get("Provision Master", [])
        if not provisions:
            return

        sub_sector_lookup = {
            record["sub_sector_id"]: record
            for record in datasets.get("Sub-Sector Master", [])
            if record.get("sub_sector_id")
        }
        sector_lookup = {
            record["sector_id"]: record.get("sector_name")
            for record in datasets.get("Sector Master", [])
            if record.get("sector_id")
        }
        law_ids = {
            record["law_id"]
            for record in datasets.get("Law Master", [])
            if record.get("law_id")
        }
        law_area_pairs = {
            (record.get("law_id"), record.get("compliance_area_id"))
            for record in datasets.get("Law_ComplianceArea_Map", [])
            if record.get("law_id") and record.get("compliance_area_id")
        }

        grouped_provisions: dict[str, list[dict[str, Any]]] = {}
        for provision in provisions:
            if provision.get("law_id") is not None:
                continue
            sub_sector_id = provision.get("sub_sector_id")
            if sub_sector_id is None:
                continue
            grouped_provisions.setdefault(sub_sector_id, []).append(provision)

        if not grouped_provisions:
            return

        provision_area_lookup: dict[str, set[str]] = {}
        for record in datasets.get("Provision_ComplianceArea_Map", []):
            provision_id = record.get("provision_id")
            compliance_area_id = record.get("compliance_area_id")
            if provision_id and compliance_area_id:
                provision_area_lookup.setdefault(provision_id, set()).add(compliance_area_id)
        for record in datasets.get("Compliance Requirement Master", []):
            provision_id = record.get("provision_id")
            compliance_area_id = record.get("compliance_area_id")
            if provision_id and compliance_area_id:
                provision_area_lookup.setdefault(provision_id, set()).add(compliance_area_id)

        for sub_sector_id, delta_provisions in grouped_provisions.items():
            law_id = self._build_delta_law_id(sub_sector_id, law_ids)
            law_ids.add(law_id)
            sub_sector_record = sub_sector_lookup.get(sub_sector_id, {})
            sector_id = sub_sector_record.get("sector_id")
            sub_sector_name = sub_sector_record.get("sub_sector_name") or sub_sector_id
            sector_name = sector_lookup.get(sector_id)
            datasets["Law Master"].append(
                {
                    "law_id": law_id,
                    "domain": "Delta Obligations",
                    "sector": sector_name,
                    "sub_sector": sub_sector_name,
                    "regulator": None,
                    "authority_level": None,
                    "document_type": "Delta Obligations",
                    "parent_law": None,
                    "law_name": f"{sub_sector_name} Delta Obligations",
                    "law_compliance_area_map": None,
                    "applicability_type": "Sub-Sector",
                    "applicability_trigger": (
                        "Importer-generated umbrella law for delta provisions without a source law ID."
                    ),
                    "active": "Yes",
                    "review_frequency": None,
                    "remarks": (
                        f"Importer-generated from delta provisions for {sub_sector_id} "
                        "because the workbook omits a Law ID."
                    ),
                }
            )
            for provision in delta_provisions:
                provision["law_id"] = law_id

            compliance_areas = sorted(
                {
                    compliance_area_id
                    for provision in delta_provisions
                    for compliance_area_id in provision_area_lookup.get(provision["provision_id"], set())
                }
            )
            for index, compliance_area_id in enumerate(compliance_areas, start=1):
                if (law_id, compliance_area_id) in law_area_pairs:
                    continue
                datasets["Law_ComplianceArea_Map"].append(
                    {
                        "map_id": f"{law_id}-LCAM-{index:03d}",
                        "law_id": law_id,
                        "compliance_area_id": compliance_area_id,
                        "active_status": "Yes",
                        "remarks": (
                            f"Importer-generated law-to-area map for delta provisions under {sub_sector_id}."
                        ),
                    }
                )
                law_area_pairs.add((law_id, compliance_area_id))

    @staticmethod
    def _build_delta_law_id(sub_sector_id: str, existing_law_ids: set[str]) -> str:
        prefix, suffix = sub_sector_id.split("-", 1)
        candidate = f"{prefix}-LAWDELTA-{suffix}"
        if candidate not in existing_law_ids:
            return candidate
        counter = 2
        while True:
            numbered_candidate = f"{candidate}-{counter:02d}"
            if numbered_candidate not in existing_law_ids:
                return numbered_candidate
            counter += 1

    def _normalize_parent_law_references(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> None:
        laws = datasets.get("Law Master", [])
        if not laws:
            return
        valid_law_ids = {
            record["law_id"]
            for record in laws
            if record.get("law_id") is not None
        }
        for record in laws:
            parent_law = record.get("parent_law")
            if parent_law is None or parent_law in valid_law_ids:
                continue
            record["parent_law"] = self._match_parent_law_reference(
                laws,
                record["law_id"],
                parent_law,
            )

    def _normalize_required_law_fields(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> None:
        for record in datasets.get("Law Master", []):
            if record.get("regulator") is None:
                record["regulator"] = "Not specified"

    def _match_parent_law_reference(
        self,
        laws: list[dict[str, Any]],
        current_law_id: str,
        parent_law_reference: str,
    ) -> str | None:
        reference_prefix = current_law_id.split("-", 1)[0]
        reference_hint = parent_law_reference
        if parent_law_reference.startswith(f"{reference_prefix}-"):
            reference_hint = parent_law_reference.split("-", 1)[1]
        normalized_hint = self._normalize_match_text(reference_hint)
        if not normalized_hint:
            return None

        candidates: list[tuple[int, int, str]] = []
        for law in laws:
            law_id = law.get("law_id")
            law_name = law.get("law_name")
            if (
                law_id is None
                or law_id == current_law_id
                or law_name is None
                or not law_id.startswith(f"{reference_prefix}-")
            ):
                continue
            normalized_name = self._normalize_match_text(law_name)
            if not normalized_name:
                continue
            if normalized_hint not in normalized_name and normalized_name not in normalized_hint:
                continue
            score = (
                1 if normalized_name.startswith(normalized_hint) else 0,
                -abs(len(normalized_name) - len(normalized_hint)),
                -len(normalized_name),
            )
            candidates.append((score[0], score[1], law_id))

        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][2]

    def _prune_incomplete_relationship_chains(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> None:
        invalid_law_map_ids = {
            record["map_id"]
            for record in datasets.get("Law_ComplianceArea_Map", [])
            if record.get("law_id") is None or record.get("compliance_area_id") is None
        }
        if invalid_law_map_ids:
            datasets["Law_ComplianceArea_Map"] = [
                record
                for record in datasets["Law_ComplianceArea_Map"]
                if record["map_id"] not in invalid_law_map_ids
            ]

        invalid_provision_ids = {
            record["provision_id"]
            for record in datasets.get("Provision_ComplianceArea_Map", [])
            if record.get("provision_id") is None or record.get("compliance_area_id") is None
        }
        if invalid_provision_ids:
            datasets["Provision_ComplianceArea_Map"] = [
                record
                for record in datasets["Provision_ComplianceArea_Map"]
                if record.get("provision_id") not in invalid_provision_ids
            ]

        invalid_compliance_ids = {
            record["compliance_id"]
            for record in datasets.get("Compliance Requirement Master", [])
            if record.get("provision_id") is None
            or record.get("compliance_area_id") is None
            or record.get("provision_id") in invalid_provision_ids
        }
        if invalid_compliance_ids:
            datasets["Compliance Requirement Master"] = [
                record
                for record in datasets["Compliance Requirement Master"]
                if record["compliance_id"] not in invalid_compliance_ids
            ]

        invalid_audit_ids = {
            record["audit_id"]
            for record in datasets.get("Audit Procedure Master", [])
            if record.get("compliance_id") is None
            or record.get("compliance_id") in invalid_compliance_ids
        }
        if invalid_audit_ids:
            datasets["Audit Procedure Master"] = [
                record
                for record in datasets["Audit Procedure Master"]
                if record["audit_id"] not in invalid_audit_ids
            ]
            datasets["Evidence Master"] = [
                record
                for record in datasets.get("Evidence Master", [])
                if record.get("audit_id") not in invalid_audit_ids
            ]
            datasets["Observation Master"] = [
                record
                for record in datasets.get("Observation Master", [])
                if record.get("audit_id") not in invalid_audit_ids
            ]

    def _normalize_audit_references(
        self,
        datasets: dict[str, list[dict[str, Any]]],
    ) -> None:
        audit_records = datasets.get("Audit Procedure Master", [])
        if not audit_records:
            return
        valid_audit_ids = {
            record["audit_id"]
            for record in audit_records
            if record.get("audit_id")
        }
        compliance_to_audit = {
            record["compliance_id"]: record["audit_id"]
            for record in audit_records
            if record.get("compliance_id") and record.get("audit_id")
        }
        for sheet_name in ["Evidence Master", "Observation Master"]:
            for record in datasets.get(sheet_name, []):
                audit_id = record.get("audit_id")
                if audit_id is None or audit_id in valid_audit_ids:
                    continue
                mapped_audit_id = compliance_to_audit.get(audit_id)
                if mapped_audit_id:
                    record["audit_id"] = mapped_audit_id

    @staticmethod
    def _normalize_match_text(value: str | None) -> str:
        if value is None:
            return ""
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _merge_duplicate_law_records(
        self,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        grouped_records: dict[str, list[dict[str, Any]]] = {}
        ordered_ids: list[str] = []
        for record in records:
            law_id = record.get("law_id")
            if law_id is None:
                continue
            if law_id not in grouped_records:
                grouped_records[law_id] = []
                ordered_ids.append(law_id)
            grouped_records[law_id].append(record)

        merged_records: list[dict[str, Any]] = []
        for law_id in ordered_ids:
            candidates = grouped_records[law_id]
            if len(candidates) == 1:
                merged_records.append(candidates[0])
                continue
            best_candidate = max(candidates, key=self._law_record_priority)
            canonical = dict(best_candidate)
            for candidate in candidates:
                if candidate is best_candidate:
                    continue
                for field, value in candidate.items():
                    if canonical.get(field) is None and value is not None:
                        canonical[field] = value
            merged_records.append(canonical)
        return merged_records

    @staticmethod
    def _law_record_priority(record: dict[str, Any]) -> tuple[int, int, int, int, int, int]:
        return (
            1 if record.get("sector") else 0,
            1 if record.get("parent_law") else 0,
            1 if record.get("regulator") else 0,
            1 if record.get("sub_sector") else 0,
            1 if record.get("law_compliance_area_map") else 0,
            sum(1 for value in record.values() if value is not None),
        )

    @staticmethod
    def _has_payload(record: dict[str, Any]) -> bool:
        ignored_fields = {"active", "active_status"}
        return any(
            value is not None
            for key, value in record.items()
            if key not in ignored_fields
        )

    def _validate_duplicate_keys(
        self,
        sheet_name: str,
        records: list[dict[str, Any]],
    ) -> None:
        pk = self.dataset_sheets[sheet_name]["pk"]
        seen: set[tuple[Any, ...]] = set()
        duplicates: list[tuple[Any, ...]] = []
        for record in records:
            key = tuple(record[column] for column in pk)
            if any(value is None for value in key):
                raise ValueError(f"{sheet_name} has blank primary key: {pk}")
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        if duplicates:
            raise ValueError(
                f"{sheet_name} has duplicate primary keys: {duplicates[:10]}"
            )

    def _validate_foreign_keys(self, datasets: dict[str, list[dict[str, Any]]]) -> None:
        key_sets = {
            sheet_name: {record[self.dataset_sheets[sheet_name]["pk"][0]] for record in records}
            for sheet_name, records in datasets.items()
            if len(self.dataset_sheets[sheet_name]["pk"]) == 1
        }
        for sheet_name, records in datasets.items():
            for child_column, parent_sheet, nullable in self.dataset_sheets[sheet_name].get(
                "fks",
                [],
            ):
                parent_values = key_sets[parent_sheet]
                invalid = []
                for record in records:
                    value = record.get(child_column)
                    if value is None and nullable:
                        continue
                    if value not in parent_values:
                        invalid.append(value)
                if invalid:
                    raise ValueError(
                        f"{sheet_name}.{child_column} has invalid FK values "
                        f"for {parent_sheet}: {invalid[:10]}"
                    )

    def _validate_enum_values(self, datasets: dict[str, list[dict[str, Any]]]) -> None:
        enum_values: dict[str, set[str]] = {}
        for record in datasets["Enum Master"]:
            enum_values.setdefault(record["enum_type"], set()).add(record["allowed_value"])
        for (sheet_name, column), enum_type in CONTROLLED_COLUMNS.items():
            allowed = enum_values.get(enum_type, set())
            invalid = [
                record[column]
                for record in datasets[sheet_name]
                if record.get(column) is not None and record[column] not in allowed
            ]
            if invalid:
                raise ValueError(
                    f"{sheet_name}.{column} has invalid {enum_type} values: "
                    f"{invalid[:10]}"
                )

    def _truncate_tables(self) -> None:
        for sheet_name in reversed(self.import_order):
            model = self.dataset_sheets[sheet_name]["model"]
            self.db.execute(delete(model))

    def _persist_sheet(
        self,
        sheet_name: str,
        records: list[dict[str, Any]],
        mode: str,
    ) -> int:
        if not records:
            return 0
        model = self.dataset_sheets[sheet_name]["model"]
        pk = self.dataset_sheets[sheet_name]["pk"]
        if sheet_name == "Law Master":
            records = self._sort_law_records_for_insert(records)
        table = model.__table__ if hasattr(model, "__table__") else model
        if mode == "truncate":
            if hasattr(model, "__mapper__"):
                self.db.bulk_insert_mappings(model, records)
            else:
                self.db.execute(table.insert(), records)
            return len(records)
        stmt = pg_insert(table).values(records)
        update_columns = {
            column.name: stmt.excluded[column.name]
            for column in table.columns
            if column.name not in pk and column.name != "created_at"
        }
        self.db.execute(
            stmt.on_conflict_do_update(index_elements=pk, set_=update_columns)
        )
        return len(records)

    def _sort_law_records_for_insert(
        self,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        records_by_id = {
            record["law_id"]: record
            for record in records
            if record.get("law_id")
        }
        ordered: list[dict[str, Any]] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(law_id: str) -> None:
            if law_id in visited or law_id in visiting:
                return
            visiting.add(law_id)
            record = records_by_id[law_id]
            parent_law = record.get("parent_law")
            if parent_law in records_by_id:
                visit(parent_law)
            visiting.remove(law_id)
            visited.add(law_id)
            ordered.append(record)

        for record in records:
            law_id = record.get("law_id")
            if law_id is None:
                continue
            visit(law_id)
        return ordered

    def _store_log(self, summary: ImportSummary) -> None:
        if not self.log_imports:
            return
        self.db.add(
            ImportLog(
                workbook_path=summary.workbook_path,
                mode=summary.mode,
                status=summary.status,
                summary=json.dumps(summary.as_dict(), default=str),
            )
        )

    def _store_failed_log(self, summary: ImportSummary) -> None:
        try:
            self._store_log(summary)
            self.db.commit()
        except Exception:
            self.db.rollback()

    @staticmethod
    def _clean_value(value: Any) -> Any:
        if pd.isna(value):
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            if re.fullmatch(r"[A-Z0-9]+--", cleaned):
                return None
            return None if cleaned.lower() in NULL_MARKERS else cleaned
        return value
