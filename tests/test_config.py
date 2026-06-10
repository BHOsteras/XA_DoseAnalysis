"""Tests for config loading."""

from pathlib import Path

import pytest

from xa_dose_analysis import config as cfg_mod
from xa_dose_analysis.config import find_config_file, load_config

TEST_CONFIG = Path(__file__).parent / "data" / "config_test.toml"


@pytest.fixture
def cfg():
    return load_config(TEST_CONFIG)


def test_paths_and_folders(cfg):
    assert cfg.config_dir == TEST_CONFIG.parent
    assert cfg.figures_dir == TEST_CONFIG.parent / "TestFigures"
    assert cfg.reports_dir == TEST_CONFIG.parent / "TestReports"


def test_data_root_falls_back_to_default(cfg):
    # The test machine's hostname is not in the config, so "default" is used.
    assert cfg.data_root == Path("/data/doses")


def test_data_root_uses_hostname_when_listed(cfg, monkeypatch):
    monkeypatch.setattr(cfg_mod.socket, "gethostname", lambda: "some-other-host")
    assert cfg.data_root == Path("/other/host/data")


def test_data_folders(cfg):
    assert cfg.ids7_folder(2025) == Path("/data/doses/IDS7/2025")
    assert cfg.dosetrack_folder("2024") == Path("/data/doses/DoseTrack - Serienivå/2024")
    assert cfg.exposure_folder() == Path("/data/doses/DoseTrack - Eksponeringsnivå")


def test_room_aliases(cfg):
    assert cfg.room_aliases == {"LAB_A": ["LAB_A_IVUS", "LAB_A_OCT"]}


def test_analysis_block(cfg):
    cardiac = cfg.analysis("cardiac")
    assert cardiac.rooms == ["LAB_A", "LAB_B"]
    assert cardiac.mapping == "pci"
    assert cardiac.max_age is None
    assert cardiac.procedure_names == ["PCI", "TAVI"]

    pci = cardiac.procedure("PCI")
    assert pci.y_max == 100
    assert pci.drl_dap == 140.0
    assert pci.drl_cak is None

    assert cardiac.procedure("TAVI").drl_dap is None


def test_analysis_optional_fields(cfg):
    children = cfg.analysis("children")
    assert children.mapping is None
    assert children.max_age == 18
    assert children.procedures == []


def test_unknown_analysis_lists_available(cfg):
    with pytest.raises(KeyError, match="cardiac"):
        cfg.analysis("does-not-exist")


def test_unknown_procedure_raises(cfg):
    with pytest.raises(KeyError, match="not configured"):
        cfg.analysis("cardiac").procedure("Unknown")


def test_find_config_file_searches_parents(tmp_path):
    (tmp_path / "config.toml").write_text('[paths]\nfigures = "F"\n', encoding="utf-8")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert find_config_file(nested) == tmp_path / "config.toml"


def test_find_config_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_config_file(tmp_path)


def test_repo_config_is_valid():
    """The real config.toml at the repository root must parse."""
    repo_config = Path(__file__).parent.parent / "config.toml"
    cfg = load_config(repo_config)
    assert "pci" in cfg.analyses
    assert cfg.analysis("pci").procedure("PCI").y_max == 100
    assert cfg.analysis("pediatric").max_age == 18


def test_aggregation_spec_has_no_overlap():
    """A column must have exactly one aggregation rule."""
    from xa_dose_analysis.columns import DT

    all_agg = DT.AGG_SUM + DT.AGG_MAX + DT.AGG_FIRST
    assert len(all_agg) == len(set(all_agg))
