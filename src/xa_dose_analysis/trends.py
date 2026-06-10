"""Dose trends over time (months, quarters or years).

Useful for following representative doses across the years of data now
available, e.g. after protocol or equipment changes.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .columns import DT, MAPPED_PROCEDURE
from .io import validate_columns
from .plotting import _save_figure

logger = logging.getLogger(__name__)

FREQUENCY_NAMES = {"M": "month", "Q": "quarter", "Y": "year"}


def trend_table(
    data: pd.DataFrame,
    procedure: str | None = None,
    freq: str = "M",
    value_col: str = DT.DAP_TOTAL,
    by_room: bool = False,
) -> pd.DataFrame:
    """Median and IQR of a dose metric per time period.

    ``freq`` is "M" (month), "Q" (quarter) or "Y" (year). Pass ``procedure``
    to restrict to one mapped procedure; ``by_room=True`` adds a per-room
    breakdown. Requires the 'Study Date' column (parsed on import).

    Returns a DataFrame with Period (as a timestamp at the period start),
    optionally Room, and n / median / q1 / q3.
    """
    if freq not in FREQUENCY_NAMES:
        raise ValueError(f"freq must be one of {sorted(FREQUENCY_NAMES)} (got '{freq}')")
    validate_columns(data, [DT.STUDY_DATE, value_col], source="merged")

    if procedure is not None:
        validate_columns(data, [MAPPED_PROCEDURE], source="merged")
        data = data[data[MAPPED_PROCEDURE] == procedure]
        if data.empty:
            raise ValueError(f"No data for procedure '{procedure}'.")

    data = data.dropna(subset=[DT.STUDY_DATE])
    periods = data[DT.STUDY_DATE].dt.to_period(freq)
    group_cols = [periods]
    names = ["Period"]
    if by_room:
        group_cols.append(data[DT.ROOM])
        names.append("Room")

    grouped = data.groupby(group_cols)[value_col]
    table = grouped.agg(
        n="count",
        median="median",
        q1=lambda s: s.quantile(0.25),
        q3=lambda s: s.quantile(0.75),
    ).reset_index(names=names)
    table["Period"] = table["Period"].dt.to_timestamp()
    return table


def plot_trend(
    data: pd.DataFrame,
    procedure: str | None = None,
    freq: str = "M",
    value_col: str = DT.DAP_TOTAL,
    drl: float | None = None,
    save: bool = False,
    figures_dir: str | Path | None = None,
) -> plt.Figure:
    """Plot the median (line) and IQR (band) of a dose metric over time.

    Optionally draws a horizontal diagnostic reference level. With
    ``save=True`` the figure is written to ``figures_dir`` (default
    ./Figures).
    """
    table = trend_table(data, procedure=procedure, freq=freq, value_col=value_col)

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(table["Period"], table["median"], marker="o", label="Median")
    ax.fill_between(table["Period"], table["q1"], table["q3"], alpha=0.25, label="IQR")
    if drl is not None:
        ax.axhline(drl, color="red", linestyle="--", label=f"DRL = {drl}")

    for _, row in table.iterrows():
        ax.annotate(
            f"n={row['n']}",
            (row["Period"], row["median"]),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
        )

    title = procedure if procedure is not None else "All procedures"
    ax.set_title(f"{title} — {value_col} per {FREQUENCY_NAMES[freq]}", fontsize=16)
    ax.set_xlabel("Period")
    ax.set_ylabel(value_col)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle=":", linewidth=0.5)
    ax.legend()
    fig.autofmt_xdate()

    if save:
        safe = title.replace("/", "-")
        _save_figure(fig, f"{safe}_trend_{freq}.png", figures_dir)
    return fig
