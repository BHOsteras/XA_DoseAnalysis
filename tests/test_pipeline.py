"""End-to-end tests of the notebook-facing pipeline API."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from conftest import ACC_BIPLANE, ACC_NORMAL  # noqa: E402
from xa_dose_analysis import pipeline  # noqa: E402
from xa_dose_analysis.columns import DT, MAPPED_PROCEDURE, UNMAPPED  # noqa: E402
from xa_dose_analysis.config import AnalysisConfig, Config, ProcedureConfig  # noqa: E402


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def cfg(tmp_path, ids7_df, dt_df):
    """A Config pointing at a tmp folder tree with the synthetic data as Excel files."""
    (tmp_path / "IDS7" / "2025").mkdir(parents=True)
    (tmp_path / "DT" / "2025").mkdir(parents=True)
    (tmp_path / "EXP" / "2025").mkdir(parents=True)
    ids7_df.to_excel(tmp_path / "IDS7" / "2025" / "ids7.xlsx", index=False)
    dt_df.to_excel(tmp_path / "DT" / "2025" / "dt.xlsx", index=False)
    dt_df.to_excel(tmp_path / "EXP" / "2025" / "exp.xlsx", index=False)

    return Config(
        config_dir=tmp_path,
        data_roots={"default": str(tmp_path)},
        ids7_subfolder="IDS7",
        dosetrack_subfolder="DT",
        exposure_subfolder="EXP",
        figures_folder="Figures",
        reports_folder="Reports",
        room_aliases={"LAB_A": ["LAB_A_IVUS"]},
        analyses={
            "test": AnalysisConfig(
                name="test",
                rooms=["LAB_A"],
                mapping="pci",
                procedures=[ProcedureConfig(name="PCI", y_max=50)],
            ),
            "children": AnalysisConfig(name="children", rooms=[], mapping=None, max_age=18),
        },
    )


@pytest.fixture
def ds(cfg):
    return pipeline.load_dataset(cfg, year=2025)


def test_load_dataset(ds):
    assert not ds.merged.empty
    assert ds.merged[DT.ACCESSION].is_unique
    # Biplane doses summed across the two Ordinal == 1 rows:
    biplane = ds.merged[ds.merged[DT.ACCESSION] == ACC_BIPLANE].iloc[0]
    assert biplane[DT.DAP_TOTAL] == pytest.approx(8.0)


def test_load_dataset_quality_counters(ds):
    q = ds.quality
    assert q.ids7_rows_read == 12
    assert q.dt_rows_read == 8
    assert q.dt_exposure_rows_removed == 2  # the Ordinal 2 and 3 rows
    assert q.missing_booking_time_removed == 1
    assert q.cancelled_removed == 1
    assert q.phantom_removed == 1
    assert q.invalid_accession_removed == 2
    assert len(q.invalid_accessions) == 2
    assert q.siemens_accessions_converted == 1
    assert q.duplicate_accessions_corrected == 1
    assert q.merged_procedures == len(ds.merged)
    # The report renders without errors:
    assert "Merged procedures" in str(q)


def test_load_dataset_with_explicit_paths(cfg, tmp_path):
    ds = pipeline.load_dataset(
        cfg,
        ids7_path=tmp_path / "IDS7" / "2025" / "ids7.xlsx",
        dt_path=tmp_path / "DT" / "2025" / "dt.xlsx",
    )
    assert not ds.merged.empty


def test_select_analysis(ds, cfg):
    data = pipeline.select_analysis(ds, cfg, "test")
    assert set(data[DT.ROOM]) == {"LAB_A"}
    assert MAPPED_PROCEDURE in data.columns
    # The synthetic descriptions match no PCI rule -> everything unmapped and recorded:
    assert (data[MAPPED_PROCEDURE] == UNMAPPED).all()
    assert ds.quality.unmapped_descriptions["test"].sum() == len(data)


def test_select_analysis_age_filter(ds, cfg):
    data = pipeline.select_analysis(ds, cfg, "children")
    # Only the biplane patient (age 8) is younger than 18:
    assert set(data[DT.ACCESSION]) == {ACC_BIPLANE}


def test_load_exposure_data_caches(cfg, tmp_path, caplog):
    df1 = pipeline.load_exposure_data(cfg, year=2025)
    assert (tmp_path / "EXP" / "2025" / "_cache_exposure_2025.pkl").is_file()
    df2 = pipeline.load_exposure_data(cfg, year=2025)
    assert len(df1) == len(df2)


def test_filter_exposures_for_procedure(ds, cfg):
    exposures = pipeline.load_exposure_data(cfg, year=2025, cache=False)
    data = ds.merged.copy()
    data[MAPPED_PROCEDURE] = "Target"
    data.loc[data[DT.ACCESSION] != ACC_NORMAL, MAPPED_PROCEDURE] = "Other"

    out = pipeline.filter_exposures_for_procedure(exposures, data, "Target")
    assert set(out[DT.ACCESSION]) == {ACC_NORMAL}


def test_plot_representative_doses(ds, cfg, tmp_path):
    data = pipeline.select_analysis(ds, cfg, "test")
    data = data.copy()
    data[MAPPED_PROCEDURE] = "PCI"  # force a match for the configured procedure
    pipeline.plot_representative_doses(data, cfg.analysis("test"), save=True, figures_dir=tmp_path)
    assert (tmp_path / "PCI.png").is_file()
