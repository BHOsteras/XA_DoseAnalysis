"""Data-quality reporting for the import/clean/merge pipeline.

A :class:`QualityReport` is filled in while the pipeline runs and gives a
structured overview of what happened to the data: how many rows each filter
removed, how well the two datasets matched, and which procedure descriptions
no mapping rule recognized.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass
class QualityReport:
    """Counters and details collected while loading, cleaning and merging."""

    ids7_rows_read: int = 0
    dt_rows_read: int = 0
    dt_exposure_rows_removed: int = 0  # rows with Ordinal != 1
    missing_booking_time_removed: int = 0
    cancelled_removed: int = 0
    phantom_removed: int = 0
    invalid_accession_removed: int = 0
    invalid_accessions: list[str] = field(default_factory=list)
    siemens_accessions_converted: int = 0
    ids7_accessions: int = 0
    ids7_accessions_not_in_dt: int = 0
    dt_accessions: int = 0
    dt_accessions_not_in_ids7: int = 0
    duplicate_accessions_corrected: int = 0
    merged_procedures: int = 0
    # Unmapped procedure descriptions with their counts, per analysis name:
    unmapped_descriptions: dict[str, pd.Series] = field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        """The counters as a two-column DataFrame (nice to display in a notebook)."""
        rows = [
            ("IDS7 rows read", self.ids7_rows_read),
            ("DoseTrack rows read", self.dt_rows_read),
            ("DoseTrack exposure rows removed (Ordinal != 1)", self.dt_exposure_rows_removed),
            ("IDS7 rows removed: missing booking time", self.missing_booking_time_removed),
            ("IDS7 rows removed: cancelled", self.cancelled_removed),
            ("IDS7 rows removed: phantom/object/animal/test", self.phantom_removed),
            ("IDS7 rows removed: invalid accession format", self.invalid_accession_removed),
            ("DoseTrack accessions converted from Siemens format", self.siemens_accessions_converted),
            ("Accession numbers in IDS7", self.ids7_accessions),
            ("... of which not in DoseTrack", self.ids7_accessions_not_in_dt),
            ("Accession numbers in DoseTrack", self.dt_accessions),
            ("... of which not in IDS7", self.dt_accessions_not_in_ids7),
            ("IDS7 rows with corrected duplicate accession", self.duplicate_accessions_corrected),
            ("Merged procedures", self.merged_procedures),
        ]
        for analysis, unmapped in self.unmapped_descriptions.items():
            rows.append((f"Unmapped procedures in analysis '{analysis}'", int(unmapped.sum())))
        return pd.DataFrame(rows, columns=["Check", "Count"])

    def to_excel(self, path: str | Path) -> None:
        """Write the report to an Excel file.

        Sheet 'Overview' holds the counters; the invalid accession numbers and
        the unmapped descriptions per analysis get their own sheets.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            self.to_frame().to_excel(writer, sheet_name="Overview", index=False)
            if self.invalid_accessions:
                pd.DataFrame({"Invalid accession": self.invalid_accessions}).to_excel(
                    writer, sheet_name="Invalid accessions", index=False
                )
            for analysis, unmapped in self.unmapped_descriptions.items():
                frame = unmapped.rename_axis("Beskrivelse").reset_index(name="Count")
                frame.to_excel(writer, sheet_name=f"Unmapped {analysis}"[:31], index=False)

    def __str__(self) -> str:
        return self.to_frame().to_string(index=False)
