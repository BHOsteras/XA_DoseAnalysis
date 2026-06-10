"""Tests for procedure mapping."""

import pandas as pd
import pytest

from xa_dose_analysis import mapping
from xa_dose_analysis.columns import IDS7, MAPPED_PROCEDURE, UNMAPPED


def make_data(*descriptions):
    return pd.DataFrame({IDS7.DESCRIPTION: list(descriptions), "DAP Total (Gy*cm2)": 1.0})


def test_simple_inclusion():
    data = make_data("RG Lever intervensjon", "RG Thorax")
    out = mapping.map_procedures(data, {"Lever": "Liver procedure"})
    assert list(out[MAPPED_PROCEDURE]) == ["Liver procedure", UNMAPPED]


def test_matching_is_case_insensitive():
    data = make_data("RG LEVER intervensjon")
    out = mapping.map_procedures(data, {"lever": "Liver procedure"})
    assert out[MAPPED_PROCEDURE].iloc[0] == "Liver procedure"


def test_multiple_inclusion_criteria():
    data = make_data("RGA Cor Ablasjon SVT m 3D", "RGA Cor Ablasjon SVT")
    out = mapping.map_procedures(data, {"Ablasjon & 3D": "Ablation with 3D"})
    assert list(out[MAPPED_PROCEDURE]) == ["Ablation with 3D", UNMAPPED]


def test_exclusion_criteria():
    data = make_data(
        "RGA Cor Ablasjon Atrieflutter",
        "RGA Cor Ablasjon Atrieflutter, RGA Cor Ablasjon Atrieflimmer",
    )
    out = mapping.map_procedures(data, {"Atrieflutter & ~Atrieflimmer": "Flutter only"})
    assert list(out[MAPPED_PROCEDURE]) == ["Flutter only", UNMAPPED]


def test_mapped_column_is_first():
    out = mapping.map_procedures(make_data("RG Lever"), {"Lever": "Liver"})
    assert out.columns[0] == MAPPED_PROCEDURE


def test_input_not_mutated():
    data = make_data("RG Lever")
    mapping.map_procedures(data, {"Lever": "Liver"})
    assert MAPPED_PROCEDURE not in data.columns


def test_no_targets_logs_warning(caplog):
    with caplog.at_level("WARNING"):
        mapping.map_procedures(make_data("RG Lever"), {"Finnes ikke": "Nothing"})
    assert "No procedures were targeted" in caplog.text


def test_conflicting_rule_is_skipped(caplog):
    data = make_data("RG Lever med kontrast")
    rules = {"Lever": "Liver A", "kontrast": "Liver B"}
    with caplog.at_level("WARNING"):
        out = mapping.map_procedures(data, rules)
    # The second rule targets a row already mapped to a different value -> skipped:
    assert out[MAPPED_PROCEDURE].iloc[0] == "Liver A"
    assert "already mapped differently" in caplog.text


def test_remapping_to_same_value_is_fine(caplog):
    data = make_data("RG Lever med kontrast")
    rules = {"Lever": "Liver", "kontrast": "Liver"}
    with caplog.at_level("WARNING"):
        out = mapping.map_procedures(data, rules)
    assert out[MAPPED_PROCEDURE].iloc[0] == "Liver"
    assert "already mapped" not in caplog.text


def test_reserved_characters_raise():
    with pytest.raises(ValueError, match="reserved character"):
        mapping.map_procedures(make_data("RG Lever & Milt"), {"Lever": "Liver"})
    with pytest.raises(ValueError, match="reserved character"):
        mapping.map_procedures(make_data("RG ~Lever"), {"Lever": "Liver"})


def test_mapping_by_registry_name():
    data = make_data("RGA Cor TAVI (int.)")
    out = mapping.map_procedures(data, "pci")
    assert out[MAPPED_PROCEDURE].iloc[0] == "TAVI"


def test_registry_has_all_dictionaries():
    assert set(mapping.MAPPING_REGISTRY) == {"pci", "dsa", "elfys", "elfys_ecr", "ped_card", "rad_xa"}
    for name in mapping.MAPPING_REGISTRY:
        result = mapping.get_mapping(name)
        assert isinstance(result, dict) and result


def test_unknown_mapping_name():
    with pytest.raises(KeyError, match="Available mappings"):
        mapping.get_mapping("does-not-exist")
