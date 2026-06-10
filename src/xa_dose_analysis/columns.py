"""Column names of the DoseTrack and IDS7 Excel exports.

Every column name used by this package is defined here and nowhere else.
If an export format changes again, this is the only file that needs editing.

The full column lists of the current export formats are documented in
``Dosetrack columns.txt`` and ``IDS7 columns.txt`` in the repository root.
"""


class DT:
    """Columns of the DoseTrack Excel export.

    One row per plane/tube and exposure: biplane equipment produces one row
    per tube, and exposure-level exports produce one row per exposure
    (``Ordinal`` numbers them; ``Ordinal == 1`` is the first exposure of the
    procedure and carries the procedure-level totals).
    """

    ACCESSION = "Accession"
    PROCEDURE = "Procedure"
    STUDY_DATE = "Study Date"
    ROOM = "Room"
    ORDINAL = "Ordinal"
    PATIENT_AGE = "Patient Age Years"
    PATIENT_SEX = "Patient Sex"

    # Procedure-level dose metrics (valid on Ordinal == 1 rows):
    DAP_TOTAL = "DAP Total (Gy*cm2)"
    DAP_MAX = "DAP Max (Gy*cm2)"
    CAK_TOTAL = "CAK Total (mGy)"
    ACQ_DAP_TOTAL = "Acquisition DAP Total (Gy*cm2)"
    ACQ_DOSE_RP_TOTAL = "Acquisition Dose RP Total (mGy)"
    ACQ_EXPOSURE_COUNT = "Acquisition Exposure Count"
    FLUORO_DAP_TOTAL = "Fluoro DAP Total (Gy*cm2)"
    FLUORO_DOSE_RP_TOTAL = "Fluoro Dose RP Total (mGy)"
    FLUORO_EXPOSURE_COUNT = "Fluoroscopy Exposure Count"
    KVP_MAX = "KVP Max (kV)"
    TOTAL_ACQ_TIME = "Total Acquisition Time (s)"
    FLUORO_ACQ_TIME = "Total Fluoro + Acquisition Time (s)"
    TOTAL_EXPOSURES = "Total Number of Exposures"
    TOTAL_FLUORO_TIME = "Total Time Of Fluoroscopy (s)"

    # Exposure-level columns (only meaningful in exposure-level exports):
    EXPOSURE_CAK = "CAK (mGy)"
    EXPOSURE_DAP = "DAP (Gy*cm2)"
    PRIMARY_ANGLE = "Positioner Primary Angle"
    SECONDARY_ANGLE = "Positioner Secondary Angle"
    ACQUISITION_PROTOCOL = "Acquisition Protocol Name"

    # Columns that must be present for the procedure-level pipeline to work:
    REQUIRED = [ACCESSION, DAP_TOTAL, CAK_TOTAL, FLUORO_ACQ_TIME, ROOM]

    # How procedure-level metrics are aggregated per accession number when a
    # procedure has several rows (biplane tubes, CBCT-like acquisitions):
    AGG_SUM = [
        ACQ_DAP_TOTAL,
        ACQ_DOSE_RP_TOTAL,
        ACQ_EXPOSURE_COUNT,
        CAK_TOTAL,
        DAP_TOTAL,
        FLUORO_DAP_TOTAL,
        FLUORO_DOSE_RP_TOTAL,
        FLUORO_EXPOSURE_COUNT,
        TOTAL_ACQ_TIME,
        FLUORO_ACQ_TIME,
        TOTAL_EXPOSURES,
        TOTAL_FLUORO_TIME,
    ]
    AGG_MAX = [DAP_MAX, KVP_MAX]
    AGG_FIRST = [STUDY_DATE, PATIENT_AGE, PATIENT_SEX, ROOM]


class IDS7:
    """Columns of the IDS7 Excel export (10 columns)."""

    ACCESSION = "Henvisnings-ID"
    DESCRIPTION = "Beskrivelse"
    BOOKED_TIME = "Bestilt dato og tidspunkt"
    CANCELLED = "Avbrutt"
    SEX = "Kjønn"
    ROOM = "Rom/modalitet (RIS)"
    CATEGORY = "Henvisningskategori (RIS)"

    # Optional column added manually for duplicate detection (anonymized
    # patient label, NOT the personal identity number):
    PATIENT = "Pasient"

    # Forbidden column: the Norwegian personal identity number must never be
    # present in the data. Its presence raises an error (privacy guard).
    PERSONAL_ID = "Fødselsnummer"

    # Pure UI columns dropped on import:
    DROP_COLUMNS = [
        "Prioritet- og lesemerkeikon",
        "Lagt til i demonstrasjon-ikon",
        "Status",
    ]

    REQUIRED = [ACCESSION, DESCRIPTION, BOOKED_TIME, ROOM]


# Columns created by this package:
MAPPED_PROCEDURE = "Mapped Procedures"
IN_DT = "Henvisning_i_dt"
IN_IDS7 = "Henvisning_i_ids7"
SOURCE_FILE = "Source_File"
