"""Synthetic IDS7 and DoseTrack test data.

The fixtures are small in-memory DataFrames covering the special cases the
pipeline must handle: invalid accession numbers, cancelled/phantom rows,
biplane procedures (several DoseTrack rows per accession), exposure-level
rows (Ordinal > 1), old Siemens PACS accessions delivered as integers, and
duplicate accession numbers on the same booking.
"""

import pandas as pd
import pytest

# Accession numbers used in the fixtures (16 characters, valid prefixes):
ACC_NORMAL = "NKRH000000000001"  # in both datasets, two IDS7 description rows
ACC_BIPLANE = "NRRH000000000002"  # two DoseTrack rows (biplane) + exposure rows
ACC_ONLY_IDS7 = "NIRH000000000003"  # not in DoseTrack
ACC_SIEMENS = "MUAH_1234567"  # 12 characters; in DoseTrack as integer 1234567
ACC_INVALID_PREFIX = "XXRH000000000005"
ACC_INVALID_LENGTH = "NKRH001"
ACC_NAT = "NKRH000000000007"  # row without booking time
ACC_CANCELLED = "NKRH000000000008"
ACC_PHANTOM = "NKRH000000000009"
ACC_DUP_IN_DT = "NKRH000000000010"  # duplicate pair: this one is in DoseTrack
ACC_DUP_NOT_IN_DT = "NKRH000000000011"  # ... and this one is not
ACC_ONLY_DT = "NKRH000000000099"  # in DoseTrack only

BOOKED = pd.Timestamp("2025-03-01 08:00")
DUP_TIME = pd.Timestamp("2025-03-02 09:30")


@pytest.fixture
def ids7_df() -> pd.DataFrame:
    def row(
        accession,
        description,
        booked=BOOKED,
        cancelled=None,
        category="RG Intervensjon",
        room="LAB_A",
        patient="PAS0001",
    ):
        return {
            "Prioritet- og lesemerkeikon": "",
            "Lagt til i demonstrasjon-ikon": "",
            "Bestilt dato og tidspunkt": booked,
            "Status": "Godkjent",
            "Avbrutt": cancelled,
            "Kjønn": "M",
            "Beskrivelse": description,
            "Rom/modalitet (RIS)": room,
            "Henvisningskategori (RIS)": category,
            "Henvisnings-ID": accession,
            "Pasient": patient,
        }

    rows = [
        # Normal procedure with two description rows (tests concatenation order):
        row(ACC_NORMAL, "RG Lever", patient="PAS0001"),
        row(ACC_NORMAL, "RG Angio abdomen", patient="PAS0001"),
        # Biplane procedure with Norwegian characters in the description:
        row(ACC_BIPLANE, "RG Caput embolisering, kar i hodet (ø, æ, å)", patient="PAS0002"),
        # In IDS7 but not in DoseTrack:
        row(ACC_ONLY_IDS7, "RG Thorax", patient="PAS0003"),
        # Old Siemens accession (12 characters with MUAH_ prefix in IDS7):
        row(ACC_SIEMENS, "RG Gammel Siemens", patient="PAS0004"),
        # Invalid accession numbers:
        row(ACC_INVALID_PREFIX, "RG Ugyldig prefiks", patient="PAS0005"),
        row(ACC_INVALID_LENGTH, "RG Ugyldig lengde", patient="PAS0006"),
        # Missing booking time:
        row(ACC_NAT, "RG Uten tidspunkt", booked=pd.NaT, patient="PAS0007"),
        # Cancelled procedure:
        row(ACC_CANCELLED, "RG Avbrutt", cancelled="Avbrutt", patient="PAS0008"),
        # Phantom/test:
        row(ACC_PHANTOM, "RG Fantom", category="X Fantom/objekt/dyr/test", patient="PAS0009"),
        # Duplicate booking: same patient and time, two accession numbers,
        # only ACC_DUP_IN_DT has DoseTrack data:
        row(ACC_DUP_IN_DT, "RG Lever intervensjon", booked=DUP_TIME, patient="PAS0010"),
        row(ACC_DUP_NOT_IN_DT, "RG Milt intervensjon", booked=DUP_TIME, patient="PAS0010"),
    ]
    df = pd.DataFrame(rows)
    df["Henvisnings-ID"] = df["Henvisnings-ID"].astype("string")
    return df


@pytest.fixture
def dt_df() -> pd.DataFrame:
    def row(
        accession,
        ordinal=1,
        dap=1.0,
        cak=10.0,
        fa_time=60.0,
        dap_max=0.5,
        kvp=80.0,
        room="LAB_A",
        age=50,
        sex="M",
        date="2025-03-01",
    ):
        return {
            "Accession": accession,
            "Ordinal": ordinal,
            "DAP Total (Gy*cm2)": dap,
            "CAK Total (mGy)": cak,
            "Total Fluoro + Acquisition Time (s)": fa_time,
            "DAP Max (Gy*cm2)": dap_max,
            "KVP Max (kV)": kvp,
            "Study Date": date,
            "Patient Age Years": age,
            "Patient Sex": sex,
            "Room": room,
        }

    rows = [
        row(ACC_NORMAL, dap=10.0, cak=100.0, fa_time=120.0),
        # Biplane: two Ordinal == 1 rows (one per tube) that must be summed,
        # plus exposure-level rows (Ordinal > 1) that must be filtered out:
        row(ACC_BIPLANE, dap=5.0, cak=50.0, fa_time=200.0, dap_max=4.0, kvp=70.0, age=8, sex="F"),
        row(ACC_BIPLANE, dap=3.0, cak=30.0, fa_time=100.0, dap_max=6.0, kvp=90.0, age=8, sex="F"),
        row(ACC_BIPLANE, ordinal=2, dap=99.0, cak=999.0, age=8, sex="F"),
        row(ACC_BIPLANE, ordinal=3, dap=99.0, cak=999.0, age=8, sex="F"),
        # Old Siemens accession as integer (as Excel delivers it):
        row(1234567, dap=2.0),
        # Duplicate-booking case:
        row(ACC_DUP_IN_DT, dap=7.0),
        # In DoseTrack but not in IDS7:
        row(ACC_ONLY_DT, dap=4.0),
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def dt_df_clean(dt_df) -> pd.DataFrame:
    """DoseTrack data as load_dosetrack would deliver it (string accessions, Ordinal == 1)."""
    df = dt_df.copy()
    df["Accession"] = df["Accession"].astype("string")
    df["Study Date"] = pd.to_datetime(df["Study Date"])
    return df[df["Ordinal"] == 1]
