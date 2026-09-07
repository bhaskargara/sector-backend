from app.repositories.regulatory_runtime import (
    _law_scope_includes_sub_sector,
    _law_scope_is_sector_wide,
)


def test_law_scope_matches_each_slash_separated_sub_sector():
    law_scope = "Cloud Service Providers / Managed Service Providers (MSP)"

    assert _law_scope_includes_sub_sector(law_scope, "Cloud Service Providers")
    assert _law_scope_includes_sub_sector(law_scope, "Managed Service Providers (MSP)")


def test_law_scope_matches_each_ampersand_separated_sub_sector():
    law_scope = "Cloud Service Providers & Data Centre & Colocation Providers"

    assert _law_scope_includes_sub_sector(law_scope, "Cloud Service Providers")
    assert _law_scope_includes_sub_sector(law_scope, "Data Centre & Colocation Providers")


def test_law_scope_does_not_split_a_slash_inside_one_sub_sector_name():
    law_scope = "Business Process Outsourcing (BPO/KPO/ITES)"

    assert _law_scope_includes_sub_sector(law_scope, law_scope)
    assert not _law_scope_includes_sub_sector(law_scope, "BPO")


def test_all_law_scope_is_not_sub_sector_specific():
    assert not _law_scope_includes_sub_sector("All", "Cloud Service Providers")


def test_all_law_scope_remains_sector_wide_when_an_applicability_matrix_maps_it():
    assert _law_scope_is_sector_wide("All")
    assert _law_scope_is_sector_wide("Banking Core")
    assert not _law_scope_is_sector_wide("Cloud Service Providers")


def test_law_scope_matches_each_semicolon_separated_sub_sector_id():
    law_scope = "MFG-SUB026; MFG-SUB027; MFG-SUB028; MFG-SUB032; MFG-SUB033"

    assert _law_scope_includes_sub_sector(
        law_scope,
        "Manufacture of electrical equipment",
        "MFG-SUB027",
    )
    assert _law_scope_includes_sub_sector(
        law_scope,
        "Repair, maintenance and installation of machinery and equipment",
        "MFG-SUB033",
    )
    assert not _law_scope_includes_sub_sector(
        law_scope,
        "Manufacture of beverages",
        "MFG-SUB010",
    )


def test_law_scope_matches_a_short_legacy_sub_sector_id():
    assert _law_scope_includes_sub_sector("SUB003", "Foreign Banks", "BANKSUB003")
