"""High-level pipeline functions — the notebook-facing API.

A typical analysis is a handful of calls:

    import xa_dose_analysis as xa

    xa.setup_logging("INFO")
    cfg = xa.load_config()
    ds = xa.load_dataset(cfg, year=2025)
    pci = xa.select_analysis(ds, cfg, "pci")
    xa.plot_representative_doses(pci, cfg.analysis("pci"))
    stats = xa.summary_by_procedure(pci)
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .cleaning import clean_all
from .columns import DT, MAPPED_PROCEDURE, UNMAPPED
from .config import AnalysisConfig, Config
from .io import filter_first_exposure, load_dosetrack, load_ids7, validate_columns
from .mapping import map_procedures
from .merging import merge_ids7_dt
from .plotting import plot_representative_dose
from .quality import QualityReport

logger = logging.getLogger(__name__)


@dataclass
class Dataset:
    """The result of loading, cleaning and merging one period of data."""

    ids7: pd.DataFrame  # cleaned IDS7 data (one row per booking line)
    dosetrack: pd.DataFrame  # cleaned procedure-level DoseTrack data
    merged: pd.DataFrame  # one row per procedure (accession number)
    quality: QualityReport


def load_dataset(
    cfg: Config,
    year: str | int | None = None,
    ids7_path: str | Path | None = None,
    dt_path: str | Path | None = None,
    manual_replace: bool = False,
) -> Dataset:
    """Load, clean and merge the IDS7 and DoseTrack data for one period.

    By default the data is read from the configured folders
    (``<data_root>/<subfolder>/<year>``); pass ``ids7_path``/``dt_path`` to
    read other folders or single Excel files instead.

    The DoseTrack data may be procedure level (Serienivå) or exposure level
    (Eksponeringsnivå) — it is reduced to ``Ordinal == 1`` either way. If the
    configured procedure-level folder does not exist, the exposure-level
    folder is used instead.

    ``manual_replace=True`` lets you resolve ambiguous duplicate accession
    numbers interactively (see
    :func:`xa_dose_analysis.cleaning.resolve_duplicate_accessions`).
    """
    quality = QualityReport()

    df_ids7 = load_ids7(ids7_path if ids7_path is not None else cfg.ids7_folder(year))
    quality.ids7_rows_read = len(df_ids7)

    df_dt_raw = load_dosetrack(
        dt_path if dt_path is not None else _resolve_dosetrack_folder(cfg, year), procedure_level=False
    )
    quality.dt_rows_read = len(df_dt_raw)
    df_dt = load_dosetrack_procedure_level(df_dt_raw)
    quality.dt_exposure_rows_removed = len(df_dt_raw) - len(df_dt)

    df_ids7, df_dt = clean_all(
        df_ids7,
        df_dt,
        room_aliases=cfg.room_aliases,
        manual_replace=manual_replace,
        quality=quality,
    )

    merged = merge_ids7_dt(df_ids7, df_dt)
    quality.merged_procedures = len(merged)

    return Dataset(ids7=df_ids7, dosetrack=df_dt, merged=merged, quality=quality)


def _resolve_dosetrack_folder(cfg: Config, year: str | int | None) -> Path:
    """The folder to read DoseTrack data from.

    Prefers the configured procedure-level folder (Serienivå); when it does
    not exist, falls back to the exposure-level folder (Eksponeringsnivå),
    which works just as well for procedure-level analysis — the files are
    only bigger.
    """
    procedure_folder = cfg.dosetrack_folder(year)
    if procedure_folder.exists():
        return procedure_folder

    exposure_folder = cfg.exposure_folder(year)
    if exposure_folder.exists():
        logger.info(
            "No procedure-level DoseTrack folder at %s; using exposure-level data from %s.",
            procedure_folder,
            exposure_folder,
        )
        return exposure_folder

    raise FileNotFoundError(
        f"No DoseTrack data found: neither {procedure_folder} nor {exposure_folder} exists."
    )


def load_dosetrack_procedure_level(df_dt_raw: pd.DataFrame) -> pd.DataFrame:
    """Reduce already-loaded DoseTrack data to procedure level (Ordinal == 1)."""
    df_dt = filter_first_exposure(df_dt_raw)
    validate_columns(df_dt, DT.REQUIRED, source="DoseTrack")
    return df_dt


def select_analysis(ds: Dataset, cfg: Config, name: str) -> pd.DataFrame:
    """Filter the merged data for one configured analysis and map its procedures.

    Applies the analysis' room filter and optional age limit, then maps the
    procedure descriptions with the analysis' mapping dictionary. Unmapped
    descriptions are recorded in ``ds.quality.unmapped_descriptions[name]``.
    """
    analysis = cfg.analysis(name)
    data = ds.merged

    if analysis.rooms:
        data = data[data[DT.ROOM].isin(analysis.rooms)]
        logger.info("Analysis '%s': %d procedures in rooms %s.", name, len(data), analysis.rooms)

    if analysis.max_age is not None:
        ages = pd.to_numeric(data[DT.PATIENT_AGE], errors="coerce")
        data = data[ages < analysis.max_age]
        logger.info("Analysis '%s': %d procedures with age < %s.", name, len(data), analysis.max_age)

    if analysis.mapping is not None:
        data = map_procedures(data, analysis.mapping)
        unmapped = data.loc[data[MAPPED_PROCEDURE] == UNMAPPED, "Beskrivelse"].value_counts()
        ds.quality.unmapped_descriptions[name] = unmapped

    return data


def load_exposure_data(
    cfg: Config,
    year: str | int | None = None,
    path: str | Path | None = None,
    cache: bool = True,
) -> pd.DataFrame:
    """Load exposure-level DoseTrack data (one row per exposure).

    These exports are large, so the combined DataFrame is cached as a pickle
    file next to the Excel files and reused on later calls. Pass
    ``cache=False`` to force a re-read (e.g. after new files were added).
    """
    folder = Path(path) if path is not None else cfg.exposure_folder(year)
    cache_file = folder / f"_cache_exposure_{year if year is not None else 'all'}.pkl"

    if cache and cache_file.is_file():
        logger.info("Loading cached exposure data from %s", cache_file)
        return pd.read_pickle(cache_file)

    df = load_dosetrack(folder, procedure_level=False)
    try:
        df.to_pickle(cache_file)
        logger.info("Cached exposure data to %s", cache_file)
    except OSError as error:  # e.g. read-only USB drive
        logger.warning("Could not write exposure cache %s: %s", cache_file, error)
    return df


def filter_exposures_for_procedure(
    exp_data: pd.DataFrame, data: pd.DataFrame, procedure: str
) -> pd.DataFrame:
    """Exposure-level rows belonging to the procedures mapped as ``procedure``.

    ``data`` is merged+mapped procedure-level data; its accession numbers for
    the given mapped procedure select the matching exposure rows.
    """
    accessions = data.loc[data[MAPPED_PROCEDURE] == procedure, DT.ACCESSION].unique()
    return exp_data[exp_data[DT.ACCESSION].isin(accessions)]


def plot_representative_doses(
    data: pd.DataFrame,
    analysis: AnalysisConfig,
    save: bool = False,
    figures_dir: str | Path | None = None,
) -> None:
    """Boxplot per configured procedure of the analysis (with its y_max)."""
    for procedure in analysis.procedures:
        plot_representative_dose(
            data, procedure.name, y_max=procedure.y_max, save=save, figures_dir=figures_dir
        )
