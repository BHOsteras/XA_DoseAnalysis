"""Comparison of representative doses against diagnostic reference levels (DRLs).

DRLs are configured per procedure in config.toml (``drl_dap`` in Gy*cm2 and/or
``drl_cak`` in mGy). :func:`compare_with_drl` joins them onto a summary table
from :func:`xa_dose_analysis.reporting.summary_by_procedure` and flags
procedures/rooms whose median exceeds the reference level.
"""

import logging

import pandas as pd

from .columns import DT
from .config import AnalysisConfig

logger = logging.getLogger(__name__)


def compare_with_drl(summary: pd.DataFrame, analysis: AnalysisConfig) -> pd.DataFrame:
    """Compare summary medians against the configured DRLs of an analysis.

    Takes the tidy table from
    :func:`~xa_dose_analysis.reporting.summary_by_procedure` and returns the
    rows for which a DRL is configured, with three extra columns:

    - ``drl``: the reference level for the row's metric,
    - ``ratio``: median / drl,
    - ``exceeds``: True when the median lies above the reference level.

    Every exceedance is also logged as a warning. Rows for metrics or
    procedures without a configured DRL are left out of the result.
    """
    drls = _configured_drls(analysis)
    if not drls:
        logger.info("No DRLs configured for analysis '%s'.", analysis.name)
        return summary.iloc[0:0].assign(drl=[], ratio=[], exceeds=[])

    keys = list(zip(summary["Procedure"], summary["Metric"], strict=True))
    has_drl = pd.Series([key in drls for key in keys], index=summary.index)

    result = summary[has_drl].copy()
    result["drl"] = [
        drls[(proc, metric)] for proc, metric in zip(result["Procedure"], result["Metric"], strict=True)
    ]
    result["ratio"] = result["median"] / result["drl"]
    result["exceeds"] = result["median"] > result["drl"]

    for _, row in result[result["exceeds"]].iterrows():
        logger.warning(
            "DRL exceeded: %s in %s has median %s = %.2f, which is %.0f%% of the DRL (%.2f).",
            row["Procedure"],
            row["Room"],
            row["Metric"],
            row["median"],
            row["ratio"] * 100,
            row["drl"],
        )
    return result


def _configured_drls(analysis: AnalysisConfig) -> dict[tuple[str, str], float]:
    """(procedure name, metric column) -> reference level, for configured DRLs."""
    drls: dict[tuple[str, str], float] = {}
    for procedure in analysis.procedures:
        if procedure.drl_dap is not None:
            drls[(procedure.name, DT.DAP_TOTAL)] = procedure.drl_dap
        if procedure.drl_cak is not None:
            drls[(procedure.name, DT.CAK_TOTAL)] = procedure.drl_cak
    return drls
