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


def test_plot_trend_by_room(data, tmp_path):
    fig = trends.plot_trend(data, procedure="PCI", freq="Y", by_room=True, save=True, figures_dir=tmp_path)
    labels = [line.get_label() for line in fig.axes[0].lines]
    assert labels == ["LAB_A (n = 3)", "LAB_B (n = 3)"]
    assert (tmp_path / "PCI_trend_Y_per_lab.png").is_file()


def test_plot_trend_by_room_without_room_column(data):
    with pytest.raises(Exception, match=DT.ROOM):
        trends.plot_trend(data.drop(columns=[DT.ROOM]), by_room=True)


def test_trend_table_single_room(data):
    table = trends.trend_table(data, procedure="PCI", freq="Y", room="LAB_A")
    assert list(table.columns) == ["Period", "n", "median", "q1", "q3"]
    assert table["n"].sum() == 3


def test_trend_table_unknown_room(data):
    with pytest.raises(ValueError, match="LAB_X"):
        trends.trend_table(data, room="LAB_X")


def test_plot_trend_single_room_has_iqr(data, tmp_path):
    fig = trends.plot_trend(data, procedure="PCI", freq="Y", room="LAB_A", save=True, figures_dir=tmp_path)
    ax = fig.axes[0]
    assert ax.collections  # the IQR band
    assert "LAB_A" in ax.get_title()
    assert (tmp_path / "PCI_trend_Y_LAB_A.png").is_file()


def test_plot_trend_rejects_by_room_with_room(data):
    with pytest.raises(ValueError, match="by_room"):
        trends.plot_trend(data, by_room=True, room="LAB_A")


def test_plot_trend_per_room(data, tmp_path):
    figures = trends.plot_trend_per_room(data, procedure="PCI", freq="Y", save=True, figures_dir=tmp_path)
    assert len(figures) == 2  # LAB_A and LAB_B
    assert all(fig.axes[0].collections for fig in figures)  # each keeps its IQR band
    tops = {fig.axes[0].get_ylim()[1] for fig in figures}
    assert len(tops) == 1  # share_y
    assert (tmp_path / "PCI_trend_Y_LAB_A.png").is_file()
    assert (tmp_path / "PCI_trend_Y_LAB_B.png").is_file()


def test_plot_trend_per_room_selected_rooms_unshared_y(data):
    figures = trends.plot_trend_per_room(data, rooms=["LAB_B"], share_y=False)
    assert len(figures) == 1
    assert "LAB_B" in figures[0].axes[0].get_title()


@pytest.fixture
def spiky_data():
    """Steady monthly doses in two labs, plus one sparse month of huge doses."""
    rng = np.random.default_rng(1)
    rows = []
    for room, base in [("LAB_A", 30.0), ("LAB_B", 32.0)]:
        for month in pd.date_range("2024-01-01", periods=12, freq="MS"):
            if (room, month.month) in {("LAB_A", 5), ("LAB_B", 8)}:
                continue  # replaced below by the outlier months
            rows += [
                (month + pd.Timedelta(days=int(day)), "PCI", room, float(value))
                for day, value in zip(rng.integers(0, 27, 10), rng.normal(base, 3.0, 10), strict=True)
            ]
    # a sparse month of huge doses, and a month with an ordinary median but a
    # quarter of its studies far above it
    rows += [
        (pd.Timestamp("2024-05-10"), "PCI", "LAB_A", 500.0),
        (pd.Timestamp("2024-05-12"), "PCI", "LAB_A", 600.0),
    ]
    rows += [
        (pd.Timestamp("2024-08-05") + pd.Timedelta(days=day), "PCI", "LAB_B", value)
        for day, value in enumerate([28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 300.0, 320.0])
    ]
    return pd.DataFrame(rows, columns=[DT.STUDY_DATE, MAPPED_PROCEDURE, DT.ROOM, DT.DAP_TOTAL])


def test_plot_trend_clips_outlier_period(spiky_data):
    fig = trends.plot_trend(spiky_data, procedure="PCI", freq="M", room="LAB_A")
    ax = fig.axes[0]
    assert ax.get_ylim()[1] < 100  # the 550 median of the sparse month is left out
    labels = [text.get_text() for text in ax.texts]
    assert "n=2\n550" in labels  # ... but its count and value are marked in the margin


def test_plot_trend_clip_false_keeps_the_whole_range(spiky_data):
    fig = trends.plot_trend(spiky_data, procedure="PCI", freq="M", room="LAB_A", clip=False)
    ax = fig.axes[0]
    assert ax.get_ylim()[1] >= 550
    assert not [text for text in ax.texts if "\n" in text.get_text()]  # nothing marked


def test_plot_trend_y_max_overrides_clipping(spiky_data):
    fig = trends.plot_trend(spiky_data, procedure="PCI", freq="M", room="LAB_A", y_max=45.0)
    assert fig.axes[0].get_ylim() == (0.0, 45.0)


def test_plot_trend_clip_keeps_the_drl_visible(spiky_data):
    fig = trends.plot_trend(spiky_data, procedure="PCI", freq="M", room="LAB_A", drl=200.0)
    assert fig.axes[0].get_ylim()[1] > 200.0


def test_plot_trend_per_room_outlier_does_not_set_the_shared_axis(spiky_data):
    figures = trends.plot_trend_per_room(spiky_data, procedure="PCI", freq="M")
    tops = {fig.axes[0].get_ylim()[1] for fig in figures}
    assert len(tops) == 1  # still shared
    assert tops.pop() < 100  # and LAB_A's sparse month no longer sets it for LAB_B


def test_plot_trend_per_room_clip_false_shares_the_tallest_axis(spiky_data):
    figures = trends.plot_trend_per_room(spiky_data, procedure="PCI", freq="M", clip=False)
    tops = {fig.axes[0].get_ylim()[1] for fig in figures}
    assert len(tops) == 1
    assert tops.pop() >= 550


def test_plot_trend_marks_a_clipped_iqr_without_moving_its_count(spiky_data):
    fig = trends.plot_trend(spiky_data, procedure="PCI", freq="M", room="LAB_B")
    labels = [text.get_text() for text in fig.axes[0].texts]
    assert "q3=100" in labels  # the band runs off the top ...
    assert "n=8" in labels  # ... but the median, and its count, stay in place
