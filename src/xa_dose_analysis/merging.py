"""Merging of cleaned IDS7 and DoseTrack data into one row per procedure.

The two datasets are matched on accession number. Before the merge each
dataset is aggregated per accession number:

- IDS7: all procedure descriptions are concatenated (sorted, comma-separated)
  into one string, which the mapping module later matches against.
- DoseTrack: dose metrics are summed over the rows of the procedure (biplane
  equipment produces one row per tube, and there may be rows for CBCT-like
  acquisitions), maxima are taken for max-type metrics, and categorical
  columns take their first value. The full specification lives in
  :data:`xa_dose_analysis.columns.DT` (``AGG_SUM``/``AGG_MAX``/``AGG_FIRST``).
"""

import logging

import pandas as pd

from .columns import DT, IDS7, IN_DT, IN_IDS7
from .io import validate_columns

logger = logging.getLogger(__name__)


def merge_ids7_dt(df_ids7: pd.DataFrame, df_dt: pd.DataFrame) -> pd.DataFrame:
    """Merge cleaned IDS7 and DoseTrack data on accession number.

    Both inputs must have been through :func:`xa_dose_analysis.cleaning.clean_all`
    (or at least the cross-flagging functions), since only accession numbers
    present in both datasets are merged.

    Returns one row per accession number with the concatenated procedure
    description from IDS7 and the aggregated dose metrics from DoseTrack.
    """
    validate_columns(df_ids7, [IDS7.ACCESSION, IDS7.DESCRIPTION, IN_DT], source="IDS7")
    validate_columns(df_dt, [DT.ACCESSION, IN_IDS7], source="DoseTrack")

    ids7_agg = _aggregation_dict(
        df_ids7,
        mandatory={IDS7.ACCESSION: "first", IDS7.DESCRIPTION: _concatenate_descriptions},
        optional={IDS7.PATIENT: "first", IDS7.SEX: "first"},
        source="IDS7",
    )
    dt_agg = _aggregation_dict(
        df_dt,
        mandatory={DT.ACCESSION: "first"},
        optional={
            **{col: "sum" for col in DT.AGG_SUM},
            **{col: "max" for col in DT.AGG_MAX},
            **{col: "first" for col in DT.AGG_FIRST},
        },
        source="DoseTrack",
    )

    ids7_per_accession = df_ids7[df_ids7[IN_DT]].groupby(IDS7.ACCESSION, as_index=False).agg(ids7_agg)
    dt_per_accession = df_dt[df_dt[IN_IDS7]].groupby(DT.ACCESSION, as_index=False).agg(dt_agg)

    data = pd.merge(
        ids7_per_accession,
        dt_per_accession,
        how="outer",
        left_on=IDS7.ACCESSION,
        right_on=DT.ACCESSION,
    )
    data = data.drop(columns=IDS7.ACCESSION)

    logger.info("Merged IDS7 and DoseTrack into %d procedures.", len(data))
    return data


def _concatenate_descriptions(series: pd.Series) -> str:
    """Concatenate all procedure descriptions of one accession into one string."""
    return ", ".join(series.sort_values().astype(str))


def _aggregation_dict(df: pd.DataFrame, mandatory: dict, optional: dict, source: str) -> dict:
    """Combine the mandatory aggregations with the optional ones present in `df`."""
    agg = dict(mandatory)
    for column, how in optional.items():
        if column in df.columns:
            agg[column] = how
        else:
            logger.info("Column '%s' not in the %s data; it will not be in the merged data.", column, source)
    return agg
