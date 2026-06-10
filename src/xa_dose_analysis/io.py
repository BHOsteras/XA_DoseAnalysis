"""Reading of IDS7 and DoseTrack Excel exports.

The loaders accept either a single ``.xlsx`` file or a folder, in which case
all Excel files in the folder tree are read and combined. On top of reading,
they normalize the data so the rest of the pipeline can rely on it:

- accession numbers become strings (Excel may deliver pure-digit accessions
  from the old Siemens PACS as integers),
- DoseTrack data is reduced to procedure level (``Ordinal == 1``) so both
  procedure-level and exposure-level exports can be used,
- the IDS7 data is checked for the forbidden personal-ID column.
"""

import logging
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from .columns import DT, IDS7, SOURCE_FILE

logger = logging.getLogger(__name__)

PathLike = str | Path
Source = PathLike | Iterable[PathLike]


class MissingColumnsError(ValueError):
    """Raised when a required column is missing from an imported dataset."""


def read_excel_files(path: Source) -> pd.DataFrame:
    """Read Excel files into one DataFrame.

    ``path`` may be a single file, a folder (every ``.xlsx`` in its tree is
    read), or a list of files/folders (e.g. several year folders).

    A ``Source_File`` column is added so each row can be traced back to the
    file it came from.
    """
    paths = [Path(path)] if isinstance(path, PathLike) else [Path(p) for p in path]

    files: list[Path] = []
    for p in paths:
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            # Skip Excel lock files (~$...) left behind by open workbooks:
            files.extend(sorted(f for f in p.rglob("*.xlsx") if not f.name.startswith("~$")))
        else:
            raise FileNotFoundError(f"No such file or folder: {p}")

    if not files:
        raise FileNotFoundError(f"No .xlsx files found under {', '.join(str(p) for p in paths)}")

    frames = []
    for file in files:
        logger.info("Reading %s", file)
        # The calamine engine ignores cell styling; openpyxl chokes on the
        # non-standard fill styles in IDS7 exports ("Fill() takes no arguments").
        df = pd.read_excel(file, engine="calamine")
        df[SOURCE_FILE] = file.name
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    logger.info(
        "Read %d rows from %d file(s) under %s",
        len(combined),
        len(files),
        ", ".join(str(p) for p in paths),
    )
    return combined


def load_ids7(path: Source) -> pd.DataFrame:
    """Load IDS7 Excel export(s) and prepare them for the pipeline.

    Drops pure UI columns, converts the accession column to string and raises
    if the forbidden personal-ID column is present.
    """
    df = read_excel_files(path)
    assert_no_personal_id(df)
    validate_columns(df, IDS7.REQUIRED, source="IDS7")

    drop = [col for col in IDS7.DROP_COLUMNS if col in df.columns]
    if drop:
        logger.info("Dropping unnecessary IDS7 columns: %s", ", ".join(drop))
        df = df.drop(columns=drop)

    if IDS7.ACCESSION in df.columns:
        df[IDS7.ACCESSION] = df[IDS7.ACCESSION].astype("string")
    return df


def load_dosetrack(path: Source, procedure_level: bool = True) -> pd.DataFrame:
    """Load DoseTrack Excel export(s) and prepare them for the pipeline.

    Converts the accession column to string. If ``procedure_level`` is True
    (the default) the data is reduced to the first exposure of each procedure
    (``Ordinal == 1``), so both pre-filtered procedure-level exports and full
    exposure-level exports can be analysed at procedure level. Pass
    ``procedure_level=False`` to keep all exposures (for e.g. angle analyses).
    """
    df = read_excel_files(path)
    validate_columns(df, [DT.ACCESSION], source="DoseTrack")

    df[DT.ACCESSION] = df[DT.ACCESSION].astype("string")
    if DT.STUDY_DATE in df.columns:
        df[DT.STUDY_DATE] = pd.to_datetime(df[DT.STUDY_DATE])

    if procedure_level:
        df = filter_first_exposure(df)
        validate_columns(df, DT.REQUIRED, source="DoseTrack")
    return df


def filter_first_exposure(df_dt: pd.DataFrame) -> pd.DataFrame:
    """Keep only ``Ordinal == 1`` rows (procedure-level data).

    The first exposure of a procedure carries the procedure-level dose totals.
    Exports that were already filtered to ``Ordinal == 1`` pass through
    unchanged. If the ``Ordinal`` column is absent the data is assumed to be
    procedure level already.
    """
    if DT.ORDINAL not in df_dt.columns:
        logger.info("No '%s' column; assuming the DoseTrack data is procedure level.", DT.ORDINAL)
        return df_dt

    first = df_dt[df_dt[DT.ORDINAL] == 1]
    removed = len(df_dt) - len(first)
    if removed:
        logger.info(
            "Reduced DoseTrack data to procedure level: kept %d of %d rows (%s == 1).",
            len(first),
            len(df_dt),
            DT.ORDINAL,
        )
    return first


def validate_columns(df: pd.DataFrame, required: list[str], source: str) -> None:
    """Raise :class:`MissingColumnsError` if any required column is missing."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise MissingColumnsError(
            f"The {source} data is missing required column(s): {', '.join(missing)}. "
            f"Available columns: {', '.join(df.columns)}"
        )


def assert_no_personal_id(df: pd.DataFrame) -> None:
    """Privacy guard: refuse to work on data containing the personal-ID column.

    The ``Pasient`` column (an anonymized patient label) should be created
    manually in Excel and the ``Fødselsnummer`` column deleted before the
    export is used here.
    """
    if IDS7.PERSONAL_ID in df.columns:
        raise ValueError(
            f"The column '{IDS7.PERSONAL_ID}' exists in the data. "
            "It must be deleted (or replaced by an anonymized 'Pasient' column) "
            "before the data can be used."
        )
