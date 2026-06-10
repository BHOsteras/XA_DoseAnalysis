"""Tests for trend analysis."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from xa_dose_analysis import trends  # noqa: E402
from xa_dose_analysis.columns import DT, MAPPED_PROCEDURE  # noqa: E402


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def data():
    rng = np.random.default_rng(0)
    dates = pd.to_datetime(
        ["2024-01-05", "2024-01-20", "2024-02-10", "2024-02-25", "2025-01-15", "2025-02-15"] * 2
    )
    return pd.DataFrame(
        {
            DT.STUDY_DATE: dates,
            MAPPED_PROCEDURE: ["PCI"] * 6 + ["TAVI"] * 6,
            DT.ROOM: ["LAB_A", "LAB_B"] * 6,
            DT.DAP_TOTAL: rng.uniform(10, 100, size=12),
        }
    )


def test_trend_table_monthly(data):
    table = trends.trend_table(data, procedure="PCI", freq="M")
    assert list(table.columns) == ["Period", "n", "median", "q1", "q3"]
    assert len(table) == 4  # Jan/Feb 2024, Jan/Feb 2025
    assert table["n"].sum() == 6
    assert (table["q1"] <= table["median"]).all()
    assert (table["median"] <= table["q3"]).all()


def test_trend_table_yearly_by_room(data):
    table = trends.trend_table(data, freq="Y", by_room=True)
    assert "Room" in table.columns
    assert len(table) == 4  # 2 years x 2 rooms
    assert table["n"].sum() == len(data)


def test_trend_table_median_value(data):
    jan = data[(data[DT.STUDY_DATE].dt.month == 1) & (data[DT.STUDY_DATE].dt.year == 2024)]
    table = trends.trend_table(data, freq="M")
    row = table[table["Period"] == pd.Timestamp("2024-01-01")].iloc[0]
    assert row["median"] == pytest.approx(jan[DT.DAP_TOTAL].median())


def test_trend_table_invalid_freq(data):
    with pytest.raises(ValueError, match="freq"):
        trends.trend_table(data, freq="W")


def test_trend_table_unknown_procedure(data):
    with pytest.raises(ValueError, match="Finnes ikke"):
        trends.trend_table(data, procedure="Finnes ikke")


def test_plot_trend_saves(data, tmp_path):
    fig = trends.plot_trend(data, procedure="PCI", freq="Q", drl=50.0, save=True, figures_dir=tmp_path)
    assert fig is not None
    assert (tmp_path / "PCI_trend_Q.png").is_file()
