"""Tests for the DRL comparison."""

import pandas as pd
import pytest

from xa_dose_analysis import drl
from xa_dose_analysis.columns import DT
from xa_dose_analysis.config import AnalysisConfig, ProcedureConfig
from xa_dose_analysis.reporting import ALL_ROOMS


@pytest.fixture
def summary():
    return pd.DataFrame(
        [
            {"Procedure": "PCI", "Room": ALL_ROOMS, "Metric": DT.DAP_TOTAL, "n": 10, "median": 60.0},
            {"Procedure": "PCI", "Room": "LAB_A", "Metric": DT.DAP_TOTAL, "n": 5, "median": 40.0},
            {"Procedure": "PCI", "Room": ALL_ROOMS, "Metric": DT.CAK_TOTAL, "n": 10, "median": 900.0},
            {"Procedure": "TAVI", "Room": ALL_ROOMS, "Metric": DT.DAP_TOTAL, "n": 4, "median": 80.0},
            {"Procedure": "PCI", "Room": ALL_ROOMS, "Metric": DT.FLUORO_ACQ_TIME, "n": 10, "median": 600.0},
        ]
    )


@pytest.fixture
def analysis():
    return AnalysisConfig(
        name="pci",
        procedures=[
            ProcedureConfig(name="PCI", drl_dap=50.0, drl_cak=1000.0),
            ProcedureConfig(name="TAVI"),  # no DRL configured
        ],
    )


def test_compare_with_drl(summary, analysis, caplog):
    with caplog.at_level("WARNING"):
        result = drl.compare_with_drl(summary, analysis)

    # Only rows with configured DRLs are returned (TAVI and time metric are not):
    assert set(result["Procedure"]) == {"PCI"}
    assert set(result["Metric"]) == {DT.DAP_TOTAL, DT.CAK_TOTAL}

    overall_dap = result[(result["Room"] == ALL_ROOMS) & (result["Metric"] == DT.DAP_TOTAL)].iloc[0]
    assert overall_dap["drl"] == 50.0
    assert overall_dap["ratio"] == pytest.approx(1.2)
    assert bool(overall_dap["exceeds"])
    assert "DRL exceeded" in caplog.text

    lab_a = result[result["Room"] == "LAB_A"].iloc[0]
    assert not bool(lab_a["exceeds"])

    cak = result[result["Metric"] == DT.CAK_TOTAL].iloc[0]
    assert cak["drl"] == 1000.0
    assert not bool(cak["exceeds"])


def test_compare_without_drls(summary):
    analysis = AnalysisConfig(name="none", procedures=[ProcedureConfig(name="PCI")])
    result = drl.compare_with_drl(summary, analysis)
    assert result.empty
    assert {"drl", "ratio", "exceeds"} <= set(result.columns)
