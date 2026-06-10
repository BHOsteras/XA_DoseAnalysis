"""Smoke tests for the plot functions (no display, Agg backend)."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from xa_dose_analysis import plotting  # noqa: E402
from xa_dose_analysis.columns import DT, MAPPED_PROCEDURE  # noqa: E402


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def mapped_data():
    rng = np.random.default_rng(0)
    n = 40
    return pd.DataFrame(
        {
            MAPPED_PROCEDURE: ["PCI"] * (n // 2) + ["TAVI"] * (n // 2),
            DT.ROOM: ["LAB_A", "LAB_B"] * (n // 2),
            DT.DAP_TOTAL: rng.uniform(1, 120, size=n),
        }
    )


@pytest.fixture
def exposure_data():
    rng = np.random.default_rng(1)
    n = 200
    return pd.DataFrame(
        {
            DT.PRIMARY_ANGLE: rng.uniform(-90, 90, size=n),
            DT.SECONDARY_ANGLE: rng.uniform(-40, 40, size=n),
            DT.EXPOSURE_CAK: rng.uniform(0, 5, size=n),
        }
    )


def test_plot_representative_dose_saves(mapped_data, tmp_path):
    fig = plotting.plot_representative_dose(mapped_data, "PCI", y_max=50, save=True, figures_dir=tmp_path)
    assert fig is not None
    assert (tmp_path / "PCI.png").is_file()


def test_plot_representative_dose_no_data(mapped_data, caplog):
    with caplog.at_level("WARNING"):
        fig = plotting.plot_representative_dose(mapped_data, "Finnes ikke")
    assert fig is None
    assert "No data" in caplog.text


def test_plot_by_procedure_saves(mapped_data, tmp_path):
    fig = plotting.plot_representative_dose_by_procedure(
        mapped_data, y_max=50, save=True, figures_dir=tmp_path
    )
    assert fig is not None
    assert (tmp_path / "oversikt.png").is_file()


def test_plot_filename_slash_replaced(mapped_data, tmp_path):
    data = mapped_data.copy()
    data[MAPPED_PROCEDURE] = "PTC/PTBD"
    plotting.plot_representative_dose(data, "PTC/PTBD", save=True, figures_dir=tmp_path)
    assert (tmp_path / "PTC-PTBD.png").is_file()


def test_heatmap_saves(exposure_data, tmp_path):
    fig = plotting.plot_air_kerma_angle_heatmap(
        exposure_data, "TAVI", bin_size=10, plot_absolute=True, save=True, figures_dir=tmp_path
    )
    assert fig is not None
    assert (tmp_path / "TAVI_AK_angles_percent.png").is_file()
    assert (tmp_path / "TAVI_AK_angles_absolute.png").is_file()


def test_heatmap_empty_data(caplog):
    empty = pd.DataFrame(columns=[DT.PRIMARY_ANGLE, DT.SECONDARY_ANGLE, DT.EXPOSURE_CAK])
    with caplog.at_level("WARNING"):
        fig = plotting.plot_air_kerma_angle_heatmap(empty, "TAVI")
    assert fig is None
