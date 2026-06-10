"""Summary statistics as DataFrames, with pretty-printing and Excel export.

The central function is :func:`summary_by_procedure`, which returns a tidy
table (one row per procedure x room x metric) with counts, median, bootstrap
confidence interval, quartiles and range. The table can be displayed in a
notebook, pretty-printed with :func:`print_summary`, or written to Excel with
:func:`export_summary`.
"""

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .columns import DT, IDS7, MAPPED_PROCEDURE

logger = logging.getLogger(__name__)

ALL_ROOMS = "All"  # value in the Room column for the across-rooms summary row
DEFAULT_METRICS = (DT.DAP_TOTAL, DT.CAK_TOTAL, DT.FLUORO_ACQ_TIME)
TIME_METRICS = {DT.FLUORO_ACQ_TIME, DT.TOTAL_ACQ_TIME, DT.TOTAL_FLUORO_TIME}


def summary_by_procedure(
    data: pd.DataFrame,
    value_cols: tuple[str, ...] = DEFAULT_METRICS,
    by_room: bool = True,
    ci: bool = True,
    n_boot: int = 10_000,
    seed: int | None = None,
) -> pd.DataFrame:
    """Summary statistics per procedure (and per room) as a tidy DataFrame.

    One row per combination of procedure, room and metric, with columns
    ``n, median, ci_low, ci_high, q1, q3, min, max``. Each procedure also
    gets an across-rooms row (Room == "All"). If the data has no
    'Mapped Procedures' column, everything is summarized as one procedure
    called "All procedures".

    ``ci`` adds a bootstrap confidence interval of the median (95%,
    ``n_boot`` resamples); pass ``seed`` for reproducible intervals.
    """
    metrics = [col for col in value_cols if col in data.columns]
    if not metrics:
        raise ValueError(f"None of the requested metrics {list(value_cols)} are in the data.")

    rng = np.random.default_rng(seed)
    if MAPPED_PROCEDURE in data.columns:
        procedure_groups = data.groupby(MAPPED_PROCEDURE, sort=True)
    else:
        procedure_groups = [("All procedures", data)]

    rows = []
    for procedure, group in procedure_groups:
        for metric in metrics:
            rows.append(_stats_row(procedure, ALL_ROOMS, metric, group[metric], ci, n_boot, rng))
            if by_room and DT.ROOM in group.columns:
                for room, room_group in group.groupby(DT.ROOM, sort=True):
                    rows.append(_stats_row(procedure, room, metric, room_group[metric], ci, n_boot, rng))

    return pd.DataFrame(rows)


def _stats_row(
    procedure: str,
    room: str,
    metric: str,
    values: pd.Series,
    ci: bool,
    n_boot: int,
    rng: np.random.Generator,
) -> dict:
    values = values.dropna().to_numpy(dtype=float)
    row = {
        "Procedure": procedure,
        "Room": room,
        "Metric": metric,
        "n": len(values),
        "median": np.median(values) if len(values) else np.nan,
        "q1": np.percentile(values, 25) if len(values) else np.nan,
        "q3": np.percentile(values, 75) if len(values) else np.nan,
        "min": values.min() if len(values) else np.nan,
        "max": values.max() if len(values) else np.nan,
    }
    if ci:
        row["ci_low"], row["ci_high"] = bootstrap_ci_median(values, n_boot=n_boot, rng=rng)
    return row


def bootstrap_ci_median(
    values: np.ndarray,
    ci_level: float = 95.0,
    n_boot: int = 10_000,
    rng: np.random.Generator | None = None,
) -> tuple[float, float]:
    """Bootstrap confidence interval of the median.

    Resamples ``values`` with replacement ``n_boot`` times and returns the
    (2.5th, 97.5th) percentiles of the resampled medians (for the default
    95% level).
    """
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return (np.nan, np.nan)
    if rng is None:
        rng = np.random.default_rng()

    medians = np.empty(n_boot)
    # Resample in chunks to keep the index matrix at a modest memory size:
    chunk_size = max(1, min(n_boot, 50_000_000 // max(len(values), 1)))
    for start in range(0, n_boot, chunk_size):
        stop = min(start + chunk_size, n_boot)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        medians[start:stop] = np.median(values[indices], axis=1)

    alpha = (100.0 - ci_level) / 2.0
    low, high = np.percentile(medians, [alpha, 100.0 - alpha])
    return float(low), float(high)


def format_min_sec(seconds: float) -> str:
    """Format a number of seconds as 'M:SS' (e.g. 754 -> '12:34')."""
    if pd.isna(seconds):
        return "-"
    minutes, secs = divmod(round(seconds), 60)
    return f"{minutes}:{secs:02d}"


def print_summary(summary: pd.DataFrame) -> None:
    """Pretty-print a table from :func:`summary_by_procedure`.

    Time metrics are shown as min:sec; doses with two decimals.
    """
    for (procedure, metric), group in summary.groupby(["Procedure", "Metric"], sort=False):
        print(f"\n{procedure} — {metric}")
        for _, row in group.iterrows():
            print("  " + _format_summary_line(row))


def _format_summary_line(row: pd.Series) -> str:
    if row["Metric"] in TIME_METRICS:
        fmt = format_min_sec
    else:

        def fmt(x):
            return "-" if pd.isna(x) else f"{x:.2f}"

    parts = [f"{row['Room']}: n = {row['n']:4d}, median = {fmt(row['median'])}"]
    if "ci_low" in row.index and not pd.isna(row.get("ci_low")):
        parts.append(f"95% CI [{fmt(row['ci_low'])} - {fmt(row['ci_high'])}]")
    parts.append(f"IQR [{fmt(row['q1'])} - {fmt(row['q3'])}]")
    parts.append(f"range ({fmt(row['min'])} - {fmt(row['max'])})")
    return ", ".join(parts)


def export_summary(tables: dict[str, pd.DataFrame], path: str | Path) -> Path:
    """Write one or more summary tables to an Excel file, one sheet per table.

    ``tables`` maps sheet names to DataFrames, e.g.
    ``{"PCI 2025": stats}``. Returns the path written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=_safe_sheet_name(name), index=False)
    logger.info("Wrote %d summary sheet(s) to %s", len(tables), path)
    return path


def _safe_sheet_name(name: str) -> str:
    """Excel sheet names: max 31 characters, no []:*?/\\ characters."""
    return re.sub(r"[\[\]:*?/\\]", "-", name)[:31]


def export_examination_codes(
    data: pd.DataFrame, output_dir: str | Path, laboratory: str | None = None
) -> list[Path]:
    """Write one text file per laboratory listing its unique examination-code combinations.

    Each line shows ``(n = count) description combination``. The lists can be
    discussed with the department to decide which procedures to report on.
    Works on both merged data and plain IDS7 data; pass ``laboratory`` to
    export a single lab. Returns the paths written.
    """
    if DT.ACCESSION in data.columns:  # merged data
        accession_col, room_col = DT.ACCESSION, DT.ROOM
    else:  # IDS7 data
        accession_col, room_col = IDS7.ACCESSION, IDS7.ROOM

    if laboratory is not None:
        data = data[data[room_col] == laboratory]
        if data.empty:
            raise ValueError(f"No rows for laboratory '{laboratory}'.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for lab, lab_data in data.groupby(room_col):
        # One description combination per accession (sorted, comma-separated):
        codes = lab_data.groupby(accession_col)[IDS7.DESCRIPTION].apply(
            lambda s: ", ".join(sorted(s.astype(str).unique()))
        )
        counts = codes.value_counts().sort_index()

        path = output_dir / f"Examination_codes_{lab}.txt"
        with open(path, "w", encoding="utf-8") as f:
            for code, count in counts.items():
                f.write(f"(n = {count}) {code}\n")
        written.append(path)
        logger.info("Wrote %d examination code(s) for %s to %s", len(counts), lab, path)
    return written
