"""Plots for representative doses and dose-by-angle distributions.

The boxplots show the median (line), the interquartile range (box), the
whisker range, and outliers (dots). Values above the y-axis limit are
annotated with the maximum and how many observations lie beyond the limit.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .columns import DT, MAPPED_PROCEDURE

logger = logging.getLogger(__name__)

DEFAULT_FIGURES_DIR = Path("Figures")


def plot_representative_dose(
    data: pd.DataFrame,
    procedure: str,
    y_max: float | None = None,
    save: bool = False,
    figures_dir: str | Path | None = None,
    whis: float | tuple[float, float] = 1.5,
) -> plt.Figure:
    """Boxplot of DAP per room for one mapped procedure.

    ``y_max`` limits the y-axis (None = automatic); rooms with values above
    the limit are annotated with their maximum and the number of values
    beyond it. ``whis`` is passed to seaborn (e.g. ``(2.5, 97.5)`` for
    percentile whiskers). With ``save=True`` the figure is written to
    ``figures_dir`` (default ./Figures) as ``<procedure>.png``.
    """
    subset = data[data[MAPPED_PROCEDURE] == procedure] if MAPPED_PROCEDURE in data.columns else data
    if subset.empty:
        logger.warning("No data for procedure '%s'; nothing plotted.", procedure)
        return None
    subset = subset.sort_values(DT.ROOM)

    fig, ax = plt.subplots(figsize=(15, 10))
    sns.boxplot(x=DT.ROOM, y=DT.DAP_TOTAL, data=subset, ax=ax, whis=whis)

    _limit_y_axis(ax, subset, DT.ROOM, DT.DAP_TOTAL, y_max)
    _add_count_labels(ax, subset, DT.ROOM)

    plt.suptitle(procedure, fontsize=30, y=1.04)
    ax.set_xlabel("Lab", fontsize=30)
    ax.set_ylabel("DAP (Gy*cm2)", fontsize=30)
    ax.grid(True, linestyle=":", linewidth=0.5)
    ax.tick_params(labelsize=15)

    if save:
        _save_figure(fig, f"{procedure}.png", figures_dir)
    return fig


def plot_representative_dose_by_procedure(
    data: pd.DataFrame,
    y_max: float | None = 20,
    save: bool = False,
    figures_dir: str | Path | None = None,
    whis: float | tuple[float, float] = 1.5,
) -> plt.Figure:
    """Boxplot of DAP per mapped procedure (all rooms together)."""
    subset = data.sort_values(MAPPED_PROCEDURE)

    fig, ax = plt.subplots(figsize=(15, 10))
    sns.boxplot(x=MAPPED_PROCEDURE, y=DT.DAP_TOTAL, data=subset, ax=ax, whis=whis)

    _limit_y_axis(ax, subset, MAPPED_PROCEDURE, DT.DAP_TOTAL, y_max, annotation_rotation=90)
    _add_count_labels(ax, subset, MAPPED_PROCEDURE, rotation=90)

    plt.suptitle("Overview Procedures", fontsize=30, y=1.07)
    ax.set_xlabel("Prosedyre", fontsize=30)
    ax.set_ylabel("DAP (Gy*cm2)", fontsize=30)
    ax.grid(True, linestyle=":", linewidth=0.5)
    ax.tick_params(labelsize=10)

    if save:
        _save_figure(fig, "oversikt.png", figures_dir)
    return fig


def plot_air_kerma_angle_heatmap(
    exp_data: pd.DataFrame,
    procedure_name: str,
    bin_size: int = 10,
    plot_absolute: bool = False,
    save: bool = False,
    figures_dir: str | Path | None = None,
) -> plt.Figure:
    """Heatmap of air kerma over the C-arm angles, from exposure-level data.

    The LAO/RAO angle (positioner primary) runs along the x-axis and the
    cranial/caudal angle (positioner secondary) along the y-axis, binned in
    ``bin_size``-degree bins. The main plot shows the percentage of the total
    air kerma per bin; ``plot_absolute=True`` also plots absolute mGy.
    """
    df = exp_data[[DT.PRIMARY_ANGLE, DT.SECONDARY_ANGLE, DT.EXPOSURE_CAK]].dropna()
    if df.empty:
        logger.warning("No exposure data with angles for '%s'; nothing plotted.", procedure_name)
        return None

    # Bins centered on multiples of bin_size, covering the full angle ranges:
    half = bin_size / 2
    primary_bins = np.arange(-half, 180 + half + bin_size, bin_size)
    primary_bins = np.unique(np.concatenate([-primary_bins[::-1], primary_bins]))
    secondary_bins = np.arange(-half, 90 + half + bin_size, bin_size)
    secondary_bins = np.unique(np.concatenate([-secondary_bins[::-1], secondary_bins]))

    df = df.assign(
        primary_bin=pd.cut(df[DT.PRIMARY_ANGLE], bins=primary_bins, right=False),
        secondary_bin=pd.cut(df[DT.SECONDARY_ANGLE], bins=secondary_bins, right=False),
    )
    heatmap = (
        df.groupby(["secondary_bin", "primary_bin"], observed=False)[DT.EXPOSURE_CAK]
        .sum()
        .unstack(fill_value=0)
    )

    x_labels = [f"{int(b.left + half)}" for b in heatmap.columns]
    y_labels = [f"{int(b.left + half)}" for b in heatmap.index]

    # Cranial angles on top:
    heatmap = heatmap.iloc[::-1]
    y_labels = y_labels[::-1]

    heatmap, x_labels, y_labels = _trim_heatmap_around_center(heatmap, x_labels, y_labels)
    zero_mask = heatmap == 0
    safe_name = procedure_name.replace("/", "-")

    if plot_absolute:
        fig_abs, ax = plt.subplots(figsize=(14, 8))
        sns.heatmap(
            heatmap,
            ax=ax,
            cmap="YlOrRd",
            linewidths=0.5,
            linecolor="grey",
            xticklabels=x_labels,
            yticklabels=y_labels,
            mask=zero_mask,
            cbar_kws={"label": "Air kerma (mGy)"},
        )
        _label_heatmap_axes(ax, f"{procedure_name} — Air kerma by C-arm angle")
        fig_abs.tight_layout()
        if save:
            _save_figure(fig_abs, f"{safe_name}_AK_angles_absolute.png", figures_dir)

    percentages = heatmap / heatmap.values.sum() * 100
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(
        percentages,
        ax=ax,
        cmap="YlOrRd",
        linewidths=0.5,
        linecolor="grey",
        xticklabels=x_labels,
        yticklabels=y_labels,
        mask=zero_mask,
        cbar_kws={"label": "% of total air kerma"},
    )
    _label_heatmap_axes(ax, f"{procedure_name} — Air kerma distribution by C-arm angle (%)")
    fig.tight_layout()
    if save:
        _save_figure(fig, f"{safe_name}_AK_angles_percent.png", figures_dir)
    return fig


def _limit_y_axis(
    ax: plt.Axes,
    data: pd.DataFrame,
    group_col: str,
    value_col: str,
    y_max: float | None,
    annotation_rotation: float = 0,
) -> None:
    """Limit the y-axis and annotate groups whose maximum lies above the limit."""
    if y_max is None or y_max <= 0:
        return
    ax.set_ylim([0, y_max])

    for i, xtick in enumerate(ax.get_xticklabels()):
        values = data.loc[data[group_col] == xtick.get_text(), value_col]
        group_max = values.max()
        if group_max > y_max:
            n_outside = int((values > y_max).sum())
            ax.annotate(
                f"Maks = {group_max:.1f}\nn$_{{(>{y_max})}}$ = {n_outside}",
                xy=(i, y_max),
                xytext=(i, y_max + y_max / 20),
                ha="center",
                va="bottom",
                fontsize=12,
                rotation=annotation_rotation,
                arrowprops={"facecolor": "black", "shrink": 0.05},
            )


def _add_count_labels(ax: plt.Axes, data: pd.DataFrame, group_col: str, rotation: float = 0) -> None:
    """Append '(n = ...)' to each x-tick label."""
    labels = []
    for xtick in ax.get_xticklabels():
        n = int((data[group_col] == xtick.get_text()).sum())
        labels.append(f"{xtick.get_text()}\n(n = {n})")
    ax.set_xticks(ax.get_xticks())  # fix the ticks before relabelling them
    ax.set_xticklabels(labels, rotation=rotation)


def _trim_heatmap_around_center(
    heatmap: pd.DataFrame, x_labels: list[str], y_labels: list[str]
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Trim empty outer bins, keeping the plot symmetric around 0 degrees."""
    col_mask = heatmap.sum(axis=0) > 0
    row_mask = heatmap.sum(axis=1) > 0
    col_center = x_labels.index("0")
    row_center = y_labels.index("0")

    col_indices = np.where(col_mask)[0]
    row_indices = np.where(row_mask)[0]
    col_extent = max(col_center - col_indices.min(), col_indices.max() - col_center) + 1
    row_extent = max(row_center - row_indices.min(), row_indices.max() - row_center) + 1

    col_start = max(0, col_center - col_extent)
    col_end = min(len(x_labels), col_center + col_extent + 1)
    row_start = max(0, row_center - row_extent)
    row_end = min(len(y_labels), row_center + row_extent + 1)

    return (
        heatmap.iloc[row_start:row_end, col_start:col_end],
        x_labels[col_start:col_end],
        y_labels[row_start:row_end],
    )


def _label_heatmap_axes(ax: plt.Axes, title: str) -> None:
    ax.set_xlabel("LAO / RAO angle (deg)\n← RAO    |    LAO →", fontsize=14)
    ax.set_ylabel("Cranial / Caudal angle (deg)\n← Caudal    |    Cranial →", fontsize=14)
    ax.set_title(title, fontsize=20)
    ax.tick_params(labelsize=10)


def _save_figure(fig: plt.Figure, filename: str, figures_dir: str | Path | None) -> Path:
    folder = Path(figures_dir) if figures_dir is not None else DEFAULT_FIGURES_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename.replace("/", "-")
    fig.savefig(path, bbox_inches="tight")
    logger.info("Saved figure to %s", path)
    return path
