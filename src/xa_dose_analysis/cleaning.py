"""Filtering and validation of IDS7 and DoseTrack data before merging.

All functions take and return DataFrames without mutating their input, so
they are safe to use with pandas copy-on-write and can be chained freely.
:func:`clean_all` runs the full sequence in the right order.
"""

import logging
import re

import pandas as pd

from .columns import DT, IDS7, IN_DT, IN_IDS7
from .io import assert_no_personal_id, validate_columns
from .quality import QualityReport

logger = logging.getLogger(__name__)

# Accession numbers must start with one of these prefixes and be 16 characters
# long (12 for converted old Siemens PACS numbers, prefix MUAH_):
VALID_ACCESSION_PREFIXES = re.compile(r"^(NORRH|NRRH|NKRH|NIRH|NNRH|NRUL|NKUL|NRRA|NRAK|NLVO|MUAH_)")
OLD_SIEMENS_FORMAT = re.compile(r"^[0-9]{7}$")


def filter_missing_booking_time(df_ids7: pd.DataFrame) -> pd.DataFrame:
    """Remove rows without a booking time ('Bestilt dato og tidspunkt')."""
    validate_columns(df_ids7, [IDS7.BOOKED_TIME], source="IDS7")
    missing = df_ids7[IDS7.BOOKED_TIME].isnull()
    logger.info("Removing %d row(s) without booking time.", int(missing.sum()))
    return df_ids7[~missing]


def filter_cancelled(df_ids7: pd.DataFrame) -> pd.DataFrame:
    """Remove cancelled procedures ('Avbrutt' == 'Avbrutt')."""
    validate_columns(df_ids7, [IDS7.CANCELLED], source="IDS7")
    cancelled = df_ids7[IDS7.CANCELLED] == "Avbrutt"
    logger.info("Removing %d cancelled procedure(s).", int(cancelled.sum()))
    return df_ids7[~cancelled]


def filter_phantom(df_ids7: pd.DataFrame) -> pd.DataFrame:
    """Remove non-human subjects (phantoms, animals, tests)."""
    validate_columns(df_ids7, [IDS7.CATEGORY], source="IDS7")
    phantom = df_ids7[IDS7.CATEGORY] == "X Fantom/objekt/dyr/test"
    logger.info("Removing %d non-human subject row(s) (phantom/object/animal/test).", int(phantom.sum()))
    return df_ids7[~phantom]


def filter_valid_accession_format(df_ids7: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows whose accession number has a valid prefix and length."""
    validate_columns(df_ids7, [IDS7.ACCESSION], source="IDS7")
    accession = df_ids7[IDS7.ACCESSION]
    is_valid = accession.str.match(VALID_ACCESSION_PREFIXES) & (
        (accession.str.len() == 16) | (accession.str.len() == 12)
    )
    n_invalid = int((~is_valid).sum())
    logger.info("Removing %d row(s) with invalid accession number format.", n_invalid)
    if n_invalid:
        logger.info("Invalid accession numbers: %s", ", ".join(accession[~is_valid].astype(str)))
    return df_ids7[is_valid]


def convert_old_siemens_accessions(df_dt: pd.DataFrame) -> pd.DataFrame:
    """Convert old Siemens PACS accession numbers (7 digits) to the Sectra format.

    In the current PACS the old numbers got the prefix 'MUAH_'; the same
    conversion is applied here so the datasets can be matched.
    """
    validate_columns(df_dt, [DT.ACCESSION], source="DoseTrack")
    is_old = df_dt[DT.ACCESSION].str.match(OLD_SIEMENS_FORMAT)
    n_old = int(is_old.sum())
    if n_old:
        logger.info(
            "Converting %d accession number(s) from the old Siemens PACS format "
            "(7 digits) by prefixing 'MUAH_'.",
            n_old,
        )
        df_dt = df_dt.copy()
        df_dt.loc[is_old, DT.ACCESSION] = "MUAH_" + df_dt.loc[is_old, DT.ACCESSION]
    return df_dt


def flag_accessions_in_dosetrack(df_ids7: pd.DataFrame, df_dt: pd.DataFrame) -> pd.DataFrame:
    """Add a boolean column flagging IDS7 accessions that exist in DoseTrack."""
    validate_columns(df_ids7, [IDS7.ACCESSION], source="IDS7")
    validate_columns(df_dt, [DT.ACCESSION], source="DoseTrack")

    df_ids7 = df_ids7.copy()
    df_ids7[IN_DT] = df_ids7[IDS7.ACCESSION].isin(df_dt[DT.ACCESSION].values)

    n_total = df_ids7[IDS7.ACCESSION].nunique()
    n_missing = df_ids7.loc[~df_ids7[IN_DT], IDS7.ACCESSION].nunique()
    logger.info("Accession numbers in IDS7: %d, of which %d are not in DoseTrack.", n_total, n_missing)
    return df_ids7


def flag_accessions_in_ids7(df_dt: pd.DataFrame, df_ids7: pd.DataFrame) -> pd.DataFrame:
    """Add a boolean column flagging DoseTrack accessions that exist in IDS7."""
    validate_columns(df_dt, [DT.ACCESSION], source="DoseTrack")
    validate_columns(df_ids7, [IDS7.ACCESSION], source="IDS7")

    df_dt = df_dt.copy()
    df_dt[IN_IDS7] = df_dt[DT.ACCESSION].isin(df_ids7[IDS7.ACCESSION].values)

    n_total = df_dt[DT.ACCESSION].nunique()
    n_missing = df_dt.loc[~df_dt[IN_IDS7], DT.ACCESSION].nunique()
    logger.info("Accession numbers in DoseTrack: %d, of which %d are not in IDS7.", n_total, n_missing)
    return df_dt


def standardize_rooms(df: pd.DataFrame, column: str, room_aliases: dict[str, list[str]]) -> pd.DataFrame:
    """Replace room-name variants with their standard name.

    ``room_aliases`` maps a standard name to its variants, e.g.
    ``{"KRH_XA3": ["KRH_XA3_Coroventis", "KRH_XA3_IVUS"]}`` (the
    ``[room_aliases]`` section of config.toml).
    """
    if column not in df.columns or not room_aliases:
        return df
    replacements = {variant: standard for standard, variants in room_aliases.items() for variant in variants}
    n_replaced = int(df[column].isin(replacements).sum())
    if n_replaced:
        logger.info("Standardized %d room name(s) in column '%s'.", n_replaced, column)
        df = df.copy()
        df[column] = df[column].replace(replacements)
    return df


def find_duplicate_accession_groups(df_ids7: pd.DataFrame) -> list[dict]:
    """Find bookings where one patient has several accession numbers at the same time.

    Requires the columns 'Pasient' (anonymized patient label), the booking
    time and the in-DoseTrack flag (see :func:`flag_accessions_in_dosetrack`).

    Returns one dict per case with keys ``patient``, ``time`` and
    ``accessions`` (a Series indexed by accession number whose values tell
    whether the accession exists in DoseTrack).
    """
    validate_columns(df_ids7, [IDS7.PATIENT, IDS7.BOOKED_TIME, IDS7.ACCESSION, IN_DT], source="IDS7")

    groups = []
    for (patient, time), booking in df_ids7.groupby([IDS7.PATIENT, IDS7.BOOKED_TIME]):
        accessions = booking.drop_duplicates(IDS7.ACCESSION).set_index(IDS7.ACCESSION)[IN_DT]
        if len(accessions) > 1:
            groups.append({"patient": patient, "time": time, "accessions": accessions})
    return groups


def resolve_duplicate_accessions(
    df_ids7: pd.DataFrame, df_dt: pd.DataFrame, manual_replace: bool = False
) -> pd.DataFrame:
    """Correct bookings that erroneously got several accession numbers.

    Occasionally a single procedure is registered in IDS7 with two accession
    numbers (e.g. one per organ) while DoseTrack only uses one of them. When
    exactly one of the accession numbers exists in DoseTrack, the others are
    overwritten with it so the dose data is matched.

    When *several* of the accession numbers exist in DoseTrack and at least
    one does not, the case is ambiguous: with ``manual_replace=True`` you are
    asked interactively which accession number to use; otherwise the case is
    only logged as a warning and left untouched.

    Requires the optional 'Pasient' column; without it the data is returned
    unchanged (with a log message), as duplicates cannot be detected.
    """
    if IDS7.PATIENT not in df_ids7.columns:
        logger.info("No '%s' column in the IDS7 data; skipping duplicate accession correction.", IDS7.PATIENT)
        return df_ids7

    if IN_DT not in df_ids7.columns:
        df_ids7 = flag_accessions_in_dosetrack(df_ids7, df_dt)

    df_ids7 = df_ids7.copy()
    changed = False
    for group in find_duplicate_accession_groups(df_ids7):
        in_dt = group["accessions"]
        if in_dt.all() or not in_dt.any():
            # All or none in DoseTrack: nothing to correct.
            continue

        candidates = in_dt[in_dt].index
        if len(candidates) > 1:
            logger.warning(
                "Ambiguous duplicate: patient %s at %s has several accession numbers with "
                "DoseTrack data (%s) and at least one without (%s).",
                group["patient"],
                group["time"],
                ", ".join(candidates),
                ", ".join(in_dt[~in_dt].index),
            )
            if manual_replace:
                replacement = _ask_user_for_accession(df_ids7, group)
            else:
                logger.warning("Pass manual_replace=True to resolve this case interactively.")
                continue
        else:
            replacement = candidates[0]

        rows = (
            (df_ids7[IDS7.PATIENT] == group["patient"])
            & (df_ids7[IDS7.BOOKED_TIME] == group["time"])
            & (~df_ids7[IN_DT])
        )
        df_ids7.loc[rows, IDS7.ACCESSION] = replacement
        changed = True
        logger.info(
            "Replaced accession number(s) %s with %s for patient %s at %s.",
            ", ".join(in_dt[~in_dt].index),
            replacement,
            group["patient"],
            group["time"],
        )

    if changed:
        df_ids7 = flag_accessions_in_dosetrack(df_ids7, df_dt)
    return df_ids7


def _ask_user_for_accession(df_ids7: pd.DataFrame, group: dict) -> str:
    """Interactively ask which accession number to use for an ambiguous case."""
    in_dt = group["accessions"]
    booking = (df_ids7[IDS7.PATIENT] == group["patient"]) & (df_ids7[IDS7.BOOKED_TIME] == group["time"])

    print(f"\nPatient {group['patient']} at {group['time']}:")
    print("Accession numbers WITHOUT data in DoseTrack:")
    for acc in in_dt[~in_dt].index:
        descriptions = df_ids7.loc[booking & (df_ids7[IDS7.ACCESSION] == acc), IDS7.DESCRIPTION]
        print(f"  {acc}: {', '.join(descriptions.astype(str))}")
    print("Accession numbers WITH data in DoseTrack:")
    for acc in in_dt[in_dt].index:
        descriptions = df_ids7.loc[booking & (df_ids7[IDS7.ACCESSION] == acc), IDS7.DESCRIPTION]
        print(f"  {acc}: {', '.join(descriptions.astype(str))}")

    while True:
        answer = input("Enter the accession number that should be used: ").strip()
        if answer in in_dt[in_dt].index:
            return answer
        print("That accession number is not among those with data in DoseTrack; try again.")


def report_patients_with_multiple_accessions_same_day(df_ids7: pd.DataFrame) -> None:
    """Log patients with several accession numbers on the same day (different times).

    Such cases are not corrected automatically; this report helps explore the
    extent of possible duplicates with slightly different booking times.
    """
    validate_columns(df_ids7, [IDS7.PATIENT, IDS7.BOOKED_TIME, IDS7.ACCESSION], source="IDS7")

    df = df_ids7[[IDS7.PATIENT, IDS7.BOOKED_TIME, IDS7.ACCESSION]].drop_duplicates()
    df = df.assign(_date=df[IDS7.BOOKED_TIME].dt.date)
    for (patient, date), day in df.groupby([IDS7.PATIENT, "_date"]):
        if day[IDS7.BOOKED_TIME].nunique() > 1 and day[IDS7.ACCESSION].nunique() > 1:
            logger.warning(
                "Patient %s has multiple accession numbers on %s: %s",
                patient,
                date,
                ", ".join(day[IDS7.ACCESSION].unique()),
            )


def clean_all(
    df_ids7: pd.DataFrame,
    df_dt: pd.DataFrame,
    room_aliases: dict[str, list[str]] | None = None,
    manual_replace: bool = False,
    quality: "QualityReport | None" = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the full cleaning sequence and return the cleaned (IDS7, DoseTrack) pair.

    Steps, in order: privacy check, room standardization (both datasets),
    IDS7 filters (booking time, cancelled, phantom, accession format),
    Siemens accession conversion, cross-flagging of accession numbers and
    duplicate-accession correction.

    Pass a :class:`~xa_dose_analysis.quality.QualityReport` as ``quality`` to
    have its counters filled in along the way.
    """
    assert_no_personal_id(df_ids7)
    if quality is None:
        quality = QualityReport()  # throwaway; keeps the bookkeeping below simple

    if room_aliases:
        df_ids7 = standardize_rooms(df_ids7, IDS7.ROOM, room_aliases)
        df_dt = standardize_rooms(df_dt, DT.ROOM, room_aliases)

    n_before = len(df_ids7)
    df_ids7 = filter_missing_booking_time(df_ids7)
    quality.missing_booking_time_removed = n_before - len(df_ids7)

    n_before = len(df_ids7)
    df_ids7 = filter_cancelled(df_ids7)
    quality.cancelled_removed = n_before - len(df_ids7)

    n_before = len(df_ids7)
    df_ids7 = filter_phantom(df_ids7)
    quality.phantom_removed = n_before - len(df_ids7)

    n_before = len(df_ids7)
    accessions_before = set(df_ids7[IDS7.ACCESSION].dropna())
    df_ids7 = filter_valid_accession_format(df_ids7)
    quality.invalid_accession_removed = n_before - len(df_ids7)
    quality.invalid_accessions = sorted(accessions_before - set(df_ids7[IDS7.ACCESSION]))

    quality.siemens_accessions_converted = int(df_dt[DT.ACCESSION].str.match(OLD_SIEMENS_FORMAT).sum())
    df_dt = convert_old_siemens_accessions(df_dt)

    df_ids7 = flag_accessions_in_dosetrack(df_ids7, df_dt)

    accession_before_resolve = df_ids7[IDS7.ACCESSION]
    df_ids7 = resolve_duplicate_accessions(df_ids7, df_dt, manual_replace=manual_replace)
    quality.duplicate_accessions_corrected = int((accession_before_resolve != df_ids7[IDS7.ACCESSION]).sum())

    df_dt = flag_accessions_in_ids7(df_dt, df_ids7)

    quality.ids7_accessions = df_ids7[IDS7.ACCESSION].nunique()
    quality.ids7_accessions_not_in_dt = df_ids7.loc[~df_ids7[IN_DT], IDS7.ACCESSION].nunique()
    quality.dt_accessions = df_dt[DT.ACCESSION].nunique()
    quality.dt_accessions_not_in_ids7 = df_dt.loc[~df_dt[IN_IDS7], DT.ACCESSION].nunique()

    return df_ids7, df_dt
