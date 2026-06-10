"""Tests for reading IDS7 and DoseTrack Excel exports."""

import pandas as pd
import pytest

from xa_dose_analysis import io
from xa_dose_analysis.columns import DT, IDS7, SOURCE_FILE


@pytest.fixture
def excel_dir(tmp_path, ids7_df, dt_df):
    """Write the synthetic data to Excel files in a small folder tree."""
    ids7_dir = tmp_path / "IDS7" / "2025"
    dt_dir = tmp_path / "DoseTrack" / "2025"
    ids7_dir.mkdir(parents=True)
    dt_dir.mkdir(parents=True)

    half = len(ids7_df) // 2
    ids7_df.iloc[:half].to_excel(ids7_dir / "2025-01 - OUS.xlsx", index=False)
    ids7_df.iloc[half:].to_excel(ids7_dir / "2025-02 - OUS.xlsx", index=False)
    dt_df.to_excel(dt_dir / "2025 - OUS.xlsx", index=False)
    return tmp_path


def test_read_excel_files_combines_folder_tree(excel_dir, ids7_df):
    df = io.read_excel_files(excel_dir / "IDS7")
    assert len(df) == len(ids7_df)
    assert set(df[SOURCE_FILE]) == {"2025-01 - OUS.xlsx", "2025-02 - OUS.xlsx"}


def test_read_excel_files_accepts_single_file(excel_dir, dt_df):
    df = io.read_excel_files(excel_dir / "DoseTrack" / "2025" / "2025 - OUS.xlsx")
    assert len(df) == len(dt_df)


def test_read_excel_files_missing_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        io.read_excel_files(tmp_path / "does-not-exist")


def test_read_excel_files_empty_folder(tmp_path):
    with pytest.raises(FileNotFoundError, match="No .xlsx files"):
        io.read_excel_files(tmp_path)


def test_load_ids7(excel_dir):
    df = io.load_ids7(excel_dir / "IDS7")
    for column in IDS7.DROP_COLUMNS:
        assert column not in df.columns
    assert df[IDS7.ACCESSION].dtype == "string"
    # Norwegian characters survive the Excel round trip:
    assert df[IDS7.DESCRIPTION].str.contains("ø, æ, å").any()


def test_load_ids7_rejects_personal_id(tmp_path, ids7_df):
    df = ids7_df.copy()
    df[IDS7.PERSONAL_ID] = "01010012345"
    df.to_excel(tmp_path / "data.xlsx", index=False)
    with pytest.raises(ValueError, match=IDS7.PERSONAL_ID):
        io.load_ids7(tmp_path / "data.xlsx")


def test_load_dosetrack(excel_dir, dt_df):
    df = io.load_dosetrack(excel_dir / "DoseTrack")
    # Exposure-level rows (Ordinal > 1) are removed:
    assert (df[DT.ORDINAL] == 1).all()
    assert len(df) == (dt_df["Ordinal"] == 1).sum()
    # Integer accessions become strings:
    assert df[DT.ACCESSION].dtype == "string"
    assert (df[DT.ACCESSION] == "1234567").any()
    # Study Date is parsed:
    assert pd.api.types.is_datetime64_any_dtype(df[DT.STUDY_DATE])


def test_load_dosetrack_keeps_exposures_when_asked(excel_dir, dt_df):
    df = io.load_dosetrack(excel_dir / "DoseTrack", procedure_level=False)
    assert len(df) == len(dt_df)


def test_load_dosetrack_missing_required_column(tmp_path, dt_df):
    df = dt_df.drop(columns=[DT.CAK_TOTAL])
    df.to_excel(tmp_path / "data.xlsx", index=False)
    with pytest.raises(io.MissingColumnsError, match="CAK Total"):
        io.load_dosetrack(tmp_path / "data.xlsx")


def test_filter_first_exposure_without_ordinal_column(dt_df):
    df = dt_df.drop(columns=[DT.ORDINAL])
    assert len(io.filter_first_exposure(df)) == len(df)
