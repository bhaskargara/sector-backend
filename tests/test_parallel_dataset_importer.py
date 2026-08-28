from app.importers.parallel_dataset_importer import (
    PARALLEL_IMPORT_ORDER,
    ParallelRegulatoryDatasetImporter,
    build_dataset_sheet_config,
)
from app.importers.pharmacy_dataset_importer import PharmacyDatasetImporter
from app.repositories.regulatory_runtime import _unique_nonempty_values


def test_parallel_dataset_config_binds_each_sector_dataset_tables():
    for dataset_key in ("bank", "it", "manufacturing"):
        config = build_dataset_sheet_config(dataset_key)

        assert set(PARALLEL_IMPORT_ORDER) == set(config)
        assert config["Applicability Matrix"]["model"].schema == dataset_key
        assert config["Law Master"]["model"].schema == dataset_key
        assert config["Observation Master"]["model"].schema == dataset_key


def test_bank_short_sub_sector_reference_is_resolved():
    importer = PharmacyDatasetImporter(db=None)
    datasets = {
        "Sub-Sector Master": [
            {
                "sub_sector_id": "BANKSUB001",
                "sector_id": "SEC004",
                "sub_sector_name": "Public Sector Banks",
            }
        ],
        "Provision Master": [
            {"provision_id": "BANK-PROV-001", "sub_sector_id": "SUB001"}
        ],
    }

    importer._normalize_sub_sector_references(datasets)

    assert datasets["Provision Master"][0]["sub_sector_id"] == "BANKSUB001"


def test_all_provision_sub_sector_marker_becomes_sector_wide():
    importer = PharmacyDatasetImporter(db=None)
    datasets = {
        "Sub-Sector Master": [],
        "Provision Master": [{"provision_id": "PROV001", "sub_sector_id": "All"}],
    }

    importer._normalize_sub_sector_references(datasets)

    assert datasets["Provision Master"][0]["sub_sector_id"] is None


def test_blank_law_sub_sector_means_sector_wide_scope():
    importer = PharmacyDatasetImporter(db=None)
    assert (
        importer._derive_law_sub_sector(
            raw_sub_sector=None,
            remarks="Sector-wide conditional law.",
            sub_sector_lookup={"SUB001": "Software Development & IT Services"},
        )
        == "All"
    )


def test_evidence_templates_are_deduplicated_in_workbook_order():
    assert _unique_nonempty_values([" Evidence A ", "Evidence A", "Evidence B", ""]) == [
        "Evidence A",
        "Evidence B",
    ]


def test_applicability_matrix_is_optional_for_parallel_sector_workbooks():
    importer = ParallelRegulatoryDatasetImporter(db=None, dataset_key="manufacturing")
    assert importer.optional_workbook_sheets == {"Applicability Matrix"}
