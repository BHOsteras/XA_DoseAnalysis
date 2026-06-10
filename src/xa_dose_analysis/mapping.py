"""Mapping of free-text procedure descriptions to standardized procedure names.

A mapping dictionary maps *criteria* to a standardized procedure name. The
criteria key is a set of case-insensitive substrings separated by ``' & '``;
a criterion starting with ``'~'`` is an exclusion. A row matches when its
(concatenated) 'Beskrivelse' contains every inclusion criterion and none of
the exclusion criteria. Example:

    "RGA Cor Ablasjon Atrieflutter (int.) & ~Atrieflimmer"
        -> "RGA Cor Ablasjon Atrieflutter (int.) m og u 3D"

The result is written to the 'Mapped Procedures' column; rows matching no
rule keep the value 'Unmapped'.

The department-specific dictionaries live in ``mapping_dicts/`` and are
available by short name through :data:`MAPPING_REGISTRY` /
:func:`get_mapping`, which is how analyses in config.toml refer to them.
"""

import logging
from collections.abc import Callable

import pandas as pd

from .columns import IDS7, MAPPED_PROCEDURE, UNMAPPED
from .io import validate_columns
from .mapping_dicts import (
    mapping_dict_DSA,
    mapping_dict_elfys,
    mapping_dict_elfys_ecr,
    mapping_dict_PCI,
    mapping_dict_ped_card_ecr,
    mapping_dict_rad_xa,
)

logger = logging.getLogger(__name__)

MAPPING_REGISTRY: dict[str, Callable[[], dict[str, str]]] = {
    "pci": mapping_dict_PCI.get_PCI_mapping_dict,
    "dsa": mapping_dict_DSA.get_DSA_mapping_dict,
    "elfys": mapping_dict_elfys.get_elfys_mapping_dict,
    "elfys_ecr": mapping_dict_elfys_ecr.get_elfys_mapping_dict,
    "ped_card": mapping_dict_ped_card_ecr.get_ped_card_mapping_dict,
    "rad_xa": mapping_dict_rad_xa.get_rad_xa_mapping_dict,
}


def get_mapping(name: str) -> dict[str, str]:
    """Return a mapping dictionary by its short name (e.g. 'pci', 'dsa')."""
    try:
        factory = MAPPING_REGISTRY[name]
    except KeyError:
        available = ", ".join(sorted(MAPPING_REGISTRY))
        raise KeyError(f"Unknown mapping '{name}'. Available mappings: {available}") from None
    return factory()


def map_procedures(df_data: pd.DataFrame, mapping: dict[str, str] | str) -> pd.DataFrame:
    """Map procedure descriptions to standardized names in 'Mapped Procedures'.

    ``mapping`` is either a mapping dictionary or the short name of one in
    :data:`MAPPING_REGISTRY`. Returns a new DataFrame with the
    'Mapped Procedures' column first; the input is not modified.

    A rule whose targets are already mapped to a *different* name is skipped
    entirely and logged as a warning, so overlapping rules in the dictionary
    are surfaced instead of silently overwritten.
    """
    if isinstance(mapping, str):
        mapping = get_mapping(mapping)

    validate_columns(df_data, [IDS7.DESCRIPTION], source="data")
    descriptions = df_data[IDS7.DESCRIPTION].astype(str)

    # '&' and '~' are reserved for the criteria syntax; descriptions containing
    # them would make the rules ambiguous.
    for reserved in ("&", "~"):
        if descriptions.str.contains(reserved, regex=False).any():
            raise ValueError(
                f"The '{IDS7.DESCRIPTION}' column contains the reserved character '{reserved}'; "
                "the mapping criteria syntax cannot be used on this data."
            )

    df_data = df_data.copy()
    df_data[MAPPED_PROCEDURE] = UNMAPPED
    # Move the mapped column to the front for readability:
    columns = [MAPPED_PROCEDURE] + [col for col in df_data.columns if col != MAPPED_PROCEDURE]
    df_data = df_data[columns]

    lowered = descriptions.str.lower()
    for key, value in mapping.items():
        targets = _match_criteria(lowered, key)
        if not targets.any():
            logger.warning("No procedures were targeted by the mapping '%s' -> '%s'.", key, value)
            continue

        conflicts = targets & ~df_data[MAPPED_PROCEDURE].isin([UNMAPPED, value])
        if conflicts.any():
            already = (
                df_data.loc[conflicts, [IDS7.DESCRIPTION, MAPPED_PROCEDURE]]
                .drop_duplicates()
                .itertuples(index=False)
            )
            conflict_lines = "; ".join(f"'{desc}' is already '{mapped}'" for desc, mapped in already)
            logger.warning(
                "Mapping '%s' -> '%s' skipped: some targets are already mapped differently (%s). "
                "Refine the mapping dictionary to avoid mapping the same procedure twice.",
                key,
                value,
                conflict_lines,
            )
            continue

        df_data.loc[targets, MAPPED_PROCEDURE] = value
        logger.info("Mapped %d procedure(s): '%s' -> '%s'", int(targets.sum()), key, value)

    n_unmapped = int((df_data[MAPPED_PROCEDURE] == UNMAPPED).sum())
    logger.info("Mapping finished: %d of %d procedures are unmapped.", n_unmapped, len(df_data))
    return df_data


def _match_criteria(lowered_descriptions: pd.Series, key: str) -> pd.Series:
    """Boolean mask of rows satisfying the inclusion/exclusion criteria in `key`."""
    criteria = key.split(" & ")
    inclusion = [c.lower() for c in criteria if not c.startswith("~")]
    exclusion = [c[1:].lower() for c in criteria if c.startswith("~")]

    matches = pd.Series(True, index=lowered_descriptions.index)
    for criterion in inclusion:
        matches &= lowered_descriptions.str.contains(criterion, regex=False)
    for criterion in exclusion:
        matches &= ~lowered_descriptions.str.contains(criterion, regex=False)
    return matches
