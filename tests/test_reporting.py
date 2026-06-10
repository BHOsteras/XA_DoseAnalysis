"""Tests for summary statistics and exports."""

import numpy as np
import pandas as pd
import pytest

from xa_dose_analysis import reporting
from xa_dose_analysis.columns import DT, IDS7, MAPPED_PROCEDURE
from xa_dose_analysis.reporting import ALL_ROOMS


@pytest.fixture
def mapped_data():
    return pd.DataFrame(
        {
            MAPPED_PROCEDURE: ["PCI"] * 4 + ["TAVI"] * 2,
            DT.ROOM: ["LAB_A", "LAB_A", "LAB_B", "LAB_B", "LAB_A", "LAB_A"],
            DT.DAP_TOTAL: [1.0, 3.0, 5.0, 7.0, 10.0, 20.0],
            DT.CAK_TOTAL: [10.0, 30.0, 50.0, 70.0, 100.0, 200.0],
            DT.FLUORO_ACQ_TIME: [60.0, 120.0, 180.0, 240.0, 300.0, 360.0],
        }
    )


def get_row(summary, procedure, room, metric):
    rows = summary[
        (summary["Procedure"] == procedure) & (summary["Room"] == room) & (summary["Metric"] == metric)
    ]
    assert len(rows) == 1
    return rows.iloc[0]


def test_summary_statistics_exact(mapped_data):
    summary = reporting.summary_by_procedure(mapped_data, ci=False)

    pci_all = get_row(summary, "PCI", ALL_ROOMS, DT.DAP_TOTAL)
    assert pci_all["n"] == 4
    assert pci_all["median"] == pytest.approx(4.0)
    assert pci_all["q1"] == pytest.approx(2.5)
    assert pci_all["q3"] == pytest.approx(5.5)
    assert pci_all["min"] == 1.0
    assert pci_all["max"] == 7.0

    pci_lab_a = get_row(summary, "PCI", "LAB_A", DT.DAP_TOTAL)
    assert pci_lab_a["n"] == 2
    assert pci_lab_a["median"] == pytest.approx(2.0)


def test_summary_without_procedure_column(mapped_data):
    data = mapped_data.drop(columns=[MAPPED_PROCEDURE])
    summary = reporting.summary_by_procedure(data, ci=False)
    assert set(summary["Procedure"]) == {"All procedures"}
    row = get_row(summary, "All procedures", ALL_ROOMS, DT.DAP_TOTAL)
    assert row["n"] == 6


def test_summary_without_room_breakdown(mapped_data):
    summary = reporting.summary_by_procedure(mapped_data, by_room=False, ci=False)
    assert set(summary["Room"]) == {ALL_ROOMS}


def test_summary_ci_is_reproducible_with_seed(mapped_data):
    a = reporting.summary_by_procedure(mapped_data, ci=True, n_boot=200, seed=42)
    b = reporting.summary_by_procedure(mapped_data, ci=True, n_boot=200, seed=42)
    pd.testing.assert_frame_equal(a, b)
    row = get_row(a, "PCI", ALL_ROOMS, DT.DAP_TOTAL)
    assert row["ci_low"] <= row["median"] <= row["ci_high"]


def test_summary_missing_metrics_raise(mapped_data):
    with pytest.raises(ValueError, match="None of the requested metrics"):
        reporting.summary_by_procedure(mapped_data[[MAPPED_PROCEDURE, DT.ROOM]])


def test_bootstrap_ci_constant_data():
    values = np.full(50, 7.0)
    low, high = reporting.bootstrap_ci_median(values, n_boot=100)
    assert low == high == 7.0


def test_bootstrap_ci_empty():
    low, high = reporting.bootstrap_ci_median(np.array([]))
    assert np.isnan(low) and np.isnan(high)


def test_format_min_sec():
    assert reporting.format_min_sec(754) == "12:34"
    assert reporting.format_min_sec(5) == "0:05"
    assert reporting.format_min_sec(float("nan")) == "-"


def test_print_summary_runs(mapped_data, capsys):
    summary = reporting.summary_by_procedure(mapped_data, ci=False)
    reporting.print_summary(summary)
    out = capsys.readouterr().out
    assert "PCI" in out
    assert "12:34" not in out  # times formatted from the fixture values
    assert "3:00" in out  # 180 s median for PCI/All exposure time


def test_export_summary(tmp_path, mapped_data):
    summary = reporting.summary_by_procedure(mapped_data, ci=False)
    path = reporting.export_summary({"PCI 2025": summary, "All/2025?": summary}, tmp_path / "out.xlsx")

    sheets = pd.read_excel(path, sheet_name=None)
    assert set(sheets) == {"PCI 2025", "All-2025-"}  # invalid characters replaced
    # Excel reads whole-number floats back as ints; compare values only:
    pd.testing.assert_frame_equal(sheets["PCI 2025"], summary, check_dtype=False)


def test_export_examination_codes(tmp_path):
    data = pd.DataFrame(
        {
            IDS7.ACCESSION: ["A1", "A1", "A2", "A3"],
            IDS7.ROOM: ["LAB_A", "LAB_A", "LAB_A", "LAB_B"],
            IDS7.DESCRIPTION: ["RG Lever", "RG Milt", "RG Lever, RG Milt", "RG Thorax"],
        }
    )
    written = reporting.export_examination_codes(data, tmp_path)
    assert {p.name for p in written} == {"Examination_codes_LAB_A.txt", "Examination_codes_LAB_B.txt"}

    lab_a = (tmp_path / "Examination_codes_LAB_A.txt").read_text(encoding="utf-8")
    # A1's two rows and A2's single combined row give the same code -> n = 2:
    assert "(n = 2) RG Lever, RG Milt" in lab_a


def test_export_examination_codes_unknown_lab(tmp_path):
    data = pd.DataFrame({IDS7.ACCESSION: ["A1"], IDS7.ROOM: ["LAB_A"], IDS7.DESCRIPTION: ["RG Lever"]})
    with pytest.raises(ValueError, match="LAB_X"):
        reporting.export_examination_codes(data, tmp_path, laboratory="LAB_X")
