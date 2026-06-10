"""Tests for reading from several files/folders at once."""

import pytest

from xa_dose_analysis import io
from xa_dose_analysis.columns import SOURCE_FILE


@pytest.fixture
def two_folders(tmp_path, dt_df):
    for year in ("2024", "2025"):
        folder = tmp_path / year
        folder.mkdir()
        dt_df.to_excel(folder / f"{year} - OUS.xlsx", index=False)
    return tmp_path


def test_read_excel_files_from_list_of_folders(two_folders, dt_df):
    df = io.read_excel_files([two_folders / "2024", two_folders / "2025"])
    assert len(df) == 2 * len(dt_df)
    assert set(df[SOURCE_FILE]) == {"2024 - OUS.xlsx", "2025 - OUS.xlsx"}


def test_read_excel_files_mixed_file_and_folder(two_folders, dt_df):
    df = io.read_excel_files([two_folders / "2024" / "2024 - OUS.xlsx", two_folders / "2025"])
    assert len(df) == 2 * len(dt_df)


def test_read_excel_files_list_with_missing_folder(two_folders):
    with pytest.raises(FileNotFoundError, match="2026"):
        io.read_excel_files([two_folders / "2024", two_folders / "2026"])


def test_read_excel_files_skips_excel_lock_files(two_folders, dt_df):
    (two_folders / "2024" / "~$2024 - OUS.xlsx").write_bytes(b"lock file")
    df = io.read_excel_files(two_folders / "2024")
    assert len(df) == len(dt_df)
