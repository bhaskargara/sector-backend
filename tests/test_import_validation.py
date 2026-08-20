import pytest

from app.importers.pharmacy_dataset_importer import PharmacyDatasetImporter


def test_duplicate_primary_key_validation_raises():
    importer = PharmacyDatasetImporter(db=None)
    records = [
        {"sector_id": "SEC001", "sector_name": "Pharmacy", "active": "Yes"},
        {"sector_id": "SEC001", "sector_name": "Duplicate", "active": "Yes"},
    ]
    with pytest.raises(ValueError, match="duplicate primary keys"):
        importer._validate_duplicate_keys("Sector Master", records)


def test_clean_value_treats_dash_as_null():
    assert PharmacyDatasetImporter._clean_value("-") is None
    assert PharmacyDatasetImporter._clean_value(" CORE ") == "CORE"
