"""Dose trends over time (months, quarters or years).

Useful for following representative doses across the years of data now
available, e.g. after protocol or equipment changes.
"""

import logging
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import pandas as pd

from .columns import DT, MAPPED_PROCEDURE
from .io import validate_columns
from .plotting import _save_figure

logger = logging.getLogger(__name__)

FREQUENCY_NAMES = {"M": "month", "Q": "quarter", "Y": "year"}

# Axis clipping: how far beyond the interquartile range of the periods a
# period may reach before it counts as an outlier, and how many studies a
# period needs before it may set the axis at all.
CLIP_FENCE_K = 3.0
CLIP_MIN_N = 5
MEDIAN_FLOOR_QUANTILE = 0.95
CLIP_PAD = 1.05
TITLE_PAD = 34


def trend_table(
    data: pd.DataFrame,
    procedure: str | None = None,
    freq: str = "M",
    value_col: str = DT.DAP_TOTAL,
    by_room: bool = False,
    room: str | None = None,
) -> pd.DataFrame:
    """Median and IQR of a dose metric per time period.

    ``freq`` is "M" (month), "Q" (quarter) or "Y" (year). Pass ``procedure``
    to restrict to one mapped procedure and ``room`` to restrict to one lab;
    ``by_room=True`` adds a per-room breakdown. Requires the 'Study Date'
    column (parsed on import).

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

    if room is not None:
        validate_columns(data, [DT.ROOM], source="merged")
        data = data[data[DT.ROOM] == room]
        if data.empty:
            raise ValueError(f"No data for lab '{room}'.")

    data = data.dropna(subset=[DT.STUDY_DATE])
    periods = data[DT.STUDY_DATE].dt.to_period(freq)
    group_cols = [periods]
    names = ["Period"]
    if by_room:
        validate_columns(data, [DT.ROOM], source="merged")
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
    by_room: bool = False,
    room: str | None = None,
    clip: bool = True,
    y_max: float | None = None,
    save: bool = False,
    figures_dir: str | Path | None = None,
) -> plt.Figure:
    """Plot the median (line) and IQR (band) of a dose metric over time.

    ``room`` restricts the plot to one lab, keeping the median-and-IQR look;
    :func:`plot_trend_per_room` draws that plot for every lab in turn. With
    ``by_room=True`` all labs go into one plot instead, as one median line
    each (no IQR bands, they overlap too much to read).

    ``clip=True`` (the default) caps the y-axis just above the bulk of the
    data, so that one extreme period cannot flatten the rest of the plot;
    what falls outside is marked in the margin above the axis (see
    :func:`_mark_clipped`). ``clip=False`` restores plain autoscaling, with
    the axis running up to the highest value. ``y_max`` sets the cap by hand
    and overrides both.

    Optionally draws a horizontal diagnostic reference level. With
    ``save=True`` the figure is written to ``figures_dir`` (default
    ./Figures).
    """
    if by_room and room is not None:
        raise ValueError("Use either by_room=True (all labs in one plot) or room=... (one lab).")
    table = trend_table(data, procedure=procedure, freq=freq, value_col=value_col, by_room=by_room, room=room)
    top = _y_limit([table], clip=clip, y_max=y_max, drl=drl, by_room=by_room)

    name = procedure if procedure is not None else "All procedures"
    fig = _draw_trend(
        table,
        title=name if room is None else f"{name} — {room}",
        value_col=value_col,
        freq=freq,
        by_room=by_room,
        drl=drl,
        top=top,
    )

    if save:
        suffix = "_per_lab" if by_room else ("" if room is None else f"_{room}")
        _save_figure(fig, _trend_filename(name, freq, suffix), figures_dir)
    return fig


def _trend_filename(name: str, freq: str, suffix: str) -> str:
    return f"{name}_trend_{freq}{suffix}.png"


def plot_trend_per_room(
    data: pd.DataFrame,
    procedure: str | None = None,
    freq: str = "M",
    value_col: str = DT.DAP_TOTAL,
    drl: float | None = None,
    rooms: list[str] | None = None,
    share_y: bool = True,
    clip: bool = True,
    y_max: float | None = None,
    save: bool = False,
    figures_dir: str | Path | None = None,
) -> list[plt.Figure]:
    """One :func:`plot_trend` figure per lab, each with its own median and IQR.

    Every lab present in the (procedure-filtered) data gets a figure, unless
    ``rooms`` lists the ones to plot. ``share_y=True`` gives all figures the
    same y-axis so the labs can be compared by eye; with ``clip=True`` that
    shared axis ignores the occasional extreme period instead of letting it
    set the scale for every lab. See :func:`plot_trend` for ``clip`` and
    ``y_max``.

    Returns the figures in the order they were drawn.
    """
    validate_columns(data, [DT.ROOM], source="merged")
    subset = data
    if procedure is not None:
        validate_columns(data, [MAPPED_PROCEDURE], source="merged")
        subset = data[data[MAPPED_PROCEDURE] == procedure]
        if subset.empty:
            raise ValueError(f"No data for procedure '{procedure}'.")
    if rooms is None:
        rooms = sorted(subset[DT.ROOM].dropna().unique())

    # Tabulated before anything is drawn: with share_y the y-axis follows from
    # every lab at once, and the saved files must show that shared axis.
    tables = [
        trend_table(data, procedure=procedure, freq=freq, value_col=value_col, room=room) for room in rooms
    ]
    shared = None
    if share_y:
        shared = _y_limit(tables, clip=clip, y_max=y_max, drl=drl)
        if shared is None:  # clip=False: the tallest lab sets the axis, as before
            shared = _data_top(tables, drl)

    name = procedure if procedure is not None else "All procedures"
    figures = []
    for room, table in zip(rooms, tables, strict=True):
        top = shared if share_y else _y_limit([table], clip=clip, y_max=y_max, drl=drl)
        fig = _draw_trend(
            table,
            title=f"{name} — {room}",
            value_col=value_col,
            freq=freq,
            by_room=False,
            drl=drl,
            top=top,
        )
        if save:
            _save_figure(fig, _trend_filename(name, freq, f"_{room}"), figures_dir)
        figures.append(fig)
    return figures


def _draw_trend(
    table: pd.DataFrame,
    *,
    title: str,
    value_col: str,
    freq: str,
    by_room: bool,
    drl: float | None,
    top: float | None,
) -> plt.Figure:
    """Draw one trend figure from an already tabulated period summary."""
    fig, ax = plt.subplots(figsize=(12, 7))
    if by_room:
        _plot_median_per_room(ax, table, top)
    else:
        _plot_median_and_iqr(ax, table, top)
    if drl is not None:
        ax.axhline(drl, color="red", linestyle="--", label=f"DRL = {drl}")

    scope = ", per lab" if by_room else ""
    # The pad is constant, clipped or not: it keeps the room above the axis
    # that the overflow markers need, and keeps the saved figures the same
    # height so that a shared y-axis lines up across labs.
    ax.set_title(f"{title} — {value_col} per {FREQUENCY_NAMES[freq]}{scope}", fontsize=16, pad=TITLE_PAD)
    ax.set_xlabel("Period")
    ax.set_ylabel(value_col)
    if top is None:
        ax.set_ylim(bottom=0)
    else:
        ax.set_ylim(0, top)
    ax.grid(True, linestyle=":", linewidth=0.5)
    ax.legend(fontsize=9)
    fig.autofmt_xdate()
    return fig


def _y_limit(
    tables: list[pd.DataFrame],
    *,
    clip: bool,
    y_max: float | None,
    drl: float | None,
    by_room: bool = False,
) -> float | None:
    """Upper y limit for a set of trend tables, or None for autoscaling."""
    if y_max is not None:
        return float(y_max)
    if not clip:
        return None
    top = _robust_top(tables, column="median" if by_room else "q3")
    if top is None:
        return None
    if drl is not None:  # a reference level above the cap would be invisible
        top = max(top, float(drl) * CLIP_PAD)
    return top


def _robust_top(
    tables: list[pd.DataFrame],
    column: str = "q3",
    fence_k: float = CLIP_FENCE_K,
    min_n: int = CLIP_MIN_N,
) -> float | None:
    """A y limit that ignores the occasional extreme period.

    The cap is the Tukey upper fence of whatever forms the top edge of the
    plot (``q3``, or the median when only medians are drawn), taken over the
    periods holding at least ``min_n`` studies: a month with two procedures
    still gets drawn, it just does not get a vote on the axis. When nothing
    lies beyond the fence the cap is simply the maximum, so an unremarkable
    plot is not clipped at all.
    """
    frames = [table for table in tables if not table.empty]
    if not frames:
        return None
    combined = pd.concat(frames, ignore_index=True)
    dense = combined[combined["n"] >= min_n]
    if dense.empty:  # every period is sparse, so let them all count
        dense = combined
    upper = dense[column].dropna()
    if upper.empty:
        return None

    q1, q3 = upper.quantile(0.25), upper.quantile(0.75)
    fence = q3 + fence_k * (q3 - q1)
    # However wide the bands get, the median line itself stays on screen.
    floor = dense["median"].quantile(MEDIAN_FLOOR_QUANTILE)
    top = max(min(upper.max(), fence), floor)
    return float(top) * CLIP_PAD if top > 0 else None


def _data_top(tables: list[pd.DataFrame], drl: float | None = None) -> float | None:
    """The highest value drawn, i.e. the limit that clips nothing."""
    values = [table["q3"].max() for table in tables if not table.empty]
    if drl is not None:
        values.append(float(drl))
    values = [value for value in values if pd.notna(value)]
    return float(max(values)) * CLIP_PAD if values else None


def _plot_median_and_iqr(ax: plt.Axes, table: pd.DataFrame, top: float | None = None) -> None:
    """One median line with an IQR band, and the count above each point."""
    (line,) = ax.plot(table["Period"], table["median"], marker="o", label="Median")
    band = ax.fill_between(table["Period"], table["q1"], table["q3"], alpha=0.25, label="IQR")
    line_color = line.get_color()
    band_color = band.get_facecolor()[0]

    for _, row in table.iterrows():
        median_out = top is not None and row["median"] > top
        if not median_out:
            _annotate_count(ax, row["Period"], row["median"], row["n"])
        if top is not None and row["q3"] > top:
            _mark_clipped(ax, row, median_out=median_out, line_color=line_color, band_color=band_color)


def _plot_median_per_room(ax: plt.Axes, table: pd.DataFrame, top: float | None = None) -> None:
    """One median line per lab, with the lab's total count in the legend."""
    for room, rows in table.groupby("Room", sort=True):
        rows = rows.sort_values("Period")
        (line,) = ax.plot(
            rows["Period"],
            rows["median"],
            marker="o",
            label=f"{room} (n = {int(rows['n'].sum())})",
        )
        if top is None:
            continue
        for _, row in rows[rows["median"] > top].iterrows():
            _mark_clipped(ax, row, median_out=True, line_color=line.get_color())


def _annotate_count(ax: plt.Axes, period: pd.Timestamp, value: float, n: float) -> None:
    ax.annotate(
        f"n={int(n)}",
        (period, value),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center",
        fontsize=8,
    )


def _mark_clipped(
    ax: plt.Axes,
    row: pd.Series,
    *,
    median_out: bool,
    line_color: str,
    band_color=None,
) -> None:
    """Mark a period that runs off the top of the axis.

    Matplotlib clips the line and the band at the top spine, so the reader
    can see them leave the plot; this adds the marker and the label that say
    how far. Both sit in the margin above the axis, at the period's x
    (data coordinates) and the top spine's y (axes coordinates), and are
    drawn with clipping switched off so they survive out there.

    A clipped median gets a filled marker, its count and its value; a period
    where only the IQR runs out keeps its count on the visible point and is
    marked with the value of q3 alone.
    """
    transform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    if median_out:
        style = {"color": line_color, "s": 70}
        label = f"n={int(row['n'])}\n{_format_value(row['median'])}"
        label_color = line_color
    else:
        style = {"color": band_color, "edgecolors": line_color, "s": 45}
        label = f"q3={_format_value(row['q3'])}"
        label_color = "0.35"

    # A scatter rather than a plot, to keep the axis' lines the data lines.
    ax.scatter(
        [row["Period"]],
        [1.0],
        transform=transform,
        marker="^",
        clip_on=False,
        zorder=5,
        **style,
    )
    ax.annotate(
        label,
        (mdates.date2num(row["Period"]), 1.0),  # annotate does not convert dates itself
        xycoords=transform,
        textcoords="offset points",
        xytext=(0, 12),
        ha="center",
        va="bottom",
        fontsize=8,
        color=label_color,
        annotation_clip=False,
    )


def _format_value(value: float) -> str:
    return f"{value:.0f}" if abs(value) >= 10 else f"{value:.1f}"
