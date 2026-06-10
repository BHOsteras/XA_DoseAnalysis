"""Tests for filtering, validation and duplicate correction."""

import pandas as pd
import pytest

from conftest import (
    ACC_BIPLANE,
    ACC_CANCELLED,
    ACC_DUP_IN_DT,
    ACC_DUP_NOT_IN_DT,
    ACC_INVALID_LENGTH,
    ACC_INVALID_PREFIX,
    ACC_NAT,
    ACC_NORMAL,
    ACC_ONLY_IDS7,
    ACC_PHANTOM,
    ACC_SIEMENS,
    DUP_TIME,
)
from xa_dose_analysis import cleaning
from xa_dose_analysis.columns import DT, IDS7, IN_DT, IN_IDS7


def accessions(df, column=IDS7.ACCESSION):
    return set(df[column])


def test_filter_missing_booking_time(ids7_df):
    out = cleaning.filter_missing_booking_time(ids7_df)
    assert ACC_NAT not in accessions(out)
    assert len(out) == len(ids7_df) - 1


def test_filter_cancelled(ids7_df):
    out = cleaning.filter_cancelled(ids7_df)
    assert ACC_CANCELLED not in accessions(out)
    assert len(out) == len(ids7_df) - 1


def test_filter_phantom(ids7_df):
    out = cleaning.filter_phantom(ids7_df)
    assert ACC_PHANTOM not in accessions(out)
    assert len(out) == len(ids7_df) - 1


def test_filter_valid_accession_format(ids7_df):
    out = cleaning.filter_valid_accession_format(ids7_df)
    assert ACC_INVALID_PREFIX not in accessions(out)
    assert ACC_INVALID_LENGTH not in accessions(out)
    # Valid 16-character and 12-character (MUAH_) accessions are kept:
    assert ACC_NORMAL in accessions(out)
    assert ACC_SIEMENS in accessions(out)


def test_filters_do_not_mutate_input(ids7_df):
    before = ids7_df.copy()
    cleaning.filter_cancelled(ids7_df)
    cleaning.filter_valid_accession_format(ids7_df)
    pd.testing.assert_frame_equal(ids7_df, before)


def test_convert_old_siemens_accessions(dt_df_clean):
    out = cleaning.convert_old_siemens_accessions(dt_df_clean)
    assert "MUAH_1234567" in accessions(out, DT.ACCESSION)
    assert "1234567" not in accessions(out, DT.ACCESSION)
    # The input is not mutated:
    assert "1234567" in accessions(dt_df_clean, DT.ACCESSION)


def test_flag_accessions_in_dosetrack(ids7_df, dt_df_clean):
    df_dt = cleaning.convert_old_siemens_accessions(dt_df_clean)
    out = cleaning.flag_accessions_in_dosetrack(ids7_df, df_dt)
    flags = out.drop_duplicates(IDS7.ACCESSION).set_index(IDS7.ACCESSION)[IN_DT]
    assert flags[ACC_NORMAL]
    assert flags[ACC_BIPLANE]
    assert flags[ACC_SIEMENS]  # matched after Siemens conversion
    assert not flags[ACC_ONLY_IDS7]
    assert not flags[ACC_DUP_NOT_IN_DT]


def test_flag_accessions_in_ids7(ids7_df, dt_df_clean):
    out = cleaning.flag_accessions_in_ids7(dt_df_clean, ids7_df)
    flags = out.drop_duplicates(DT.ACCESSION).set_index(DT.ACCESSION)[IN_IDS7]
    assert flags[ACC_NORMAL]
    assert not flags["NKRH000000000099"]  # only in DoseTrack
    assert not flags["1234567"]  # only matches after conversion


def test_standardize_rooms(ids7_df):
    df = ids7_df.copy()
    df.loc[df[IDS7.ACCESSION] == ACC_NORMAL, IDS7.ROOM] = "LAB_A_IVUS"
    out = cleaning.standardize_rooms(df, IDS7.ROOM, {"LAB_A": ["LAB_A_IVUS", "LAB_A_OCT"]})
    assert "LAB_A_IVUS" not in set(out[IDS7.ROOM])
    assert (out.loc[out[IDS7.ACCESSION] == ACC_NORMAL, IDS7.ROOM] == "LAB_A").all()


def test_resolve_duplicate_accessions_auto_fix(ids7_df, dt_df_clean):
    df_dt = cleaning.convert_old_siemens_accessions(dt_df_clean)
    df_ids7 = cleaning.flag_accessions_in_dosetrack(ids7_df, df_dt)

    out = cleaning.resolve_duplicate_accessions(df_ids7, df_dt)

    # The accession without DoseTrack data was rewritten to the one with data:
    assert ACC_DUP_NOT_IN_DT not in accessions(out)
    dup_rows = out[(out["Pasient"] == "PAS0010") & (out[IDS7.BOOKED_TIME] == DUP_TIME)]
    assert (dup_rows[IDS7.ACCESSION] == ACC_DUP_IN_DT).all()
    # The in-DoseTrack flag was refreshed after the correction:
    assert dup_rows[IN_DT].all()
    # Untouched rows keep their accession:
    assert ACC_ONLY_IDS7 in accessions(out)


def test_resolve_duplicate_accessions_ambiguous_untouched(ids7_df, dt_df_clean, caplog):
    # Make the duplicate case ambiguous: both a second in-DT accession and one without.
    extra = ids7_df[ids7_df[IDS7.ACCESSION] == ACC_DUP_IN_DT].copy()
    extra[IDS7.ACCESSION] = ACC_NORMAL  # ACC_NORMAL is in DoseTrack
    extra["Pasient"] = "PAS0010"
    extra[IDS7.BOOKED_TIME] = DUP_TIME
    df_ids7 = pd.concat([ids7_df, extra], ignore_index=True)

    df_dt = cleaning.convert_old_siemens_accessions(dt_df_clean)
    df_ids7 = cleaning.flag_accessions_in_dosetrack(df_ids7, df_dt)

    with caplog.at_level("WARNING"):
        out = cleaning.resolve_duplicate_accessions(df_ids7, df_dt)

    # The ambiguous case is logged but not changed:
    assert "Ambiguous duplicate" in caplog.text
    assert ACC_DUP_NOT_IN_DT in accessions(out)


def test_resolve_duplicate_accessions_without_patient_column(ids7_df, dt_df_clean):
    df_ids7 = ids7_df.drop(columns=["Pasient"])
    out = cleaning.resolve_duplicate_accessions(df_ids7, dt_df_clean)
    assert ACC_DUP_NOT_IN_DT in accessions(out)  # nothing corrected, no crash


def test_clean_all(ids7_df, dt_df_clean):
    df_ids7, df_dt = cleaning.clean_all(ids7_df, dt_df_clean)

    removed = {ACC_NAT, ACC_CANCELLED, ACC_PHANTOM, ACC_INVALID_PREFIX, ACC_INVALID_LENGTH, ACC_DUP_NOT_IN_DT}
    assert accessions(df_ids7).isdisjoint(removed)
    assert IN_DT in df_ids7.columns
    assert IN_IDS7 in df_dt.columns
    assert "MUAH_1234567" in accessions(df_dt, DT.ACCESSION)


def test_clean_all_rejects_personal_id(ids7_df, dt_df_clean):
    df = ids7_df.copy()
    df[IDS7.PERSONAL_ID] = "01010012345"
    with pytest.raises(ValueError, match=IDS7.PERSONAL_ID):
        cleaning.clean_all(df, dt_df_clean)


def test_report_multiple_accessions_same_day(ids7_df, caplog):
    # Same patient, same day, different times and accessions:
    df = ids7_df.copy()
    df.loc[df[IDS7.ACCESSION] == ACC_ONLY_IDS7, "Pasient"] = "PAS0001"
    df.loc[df[IDS7.ACCESSION] == ACC_ONLY_IDS7, IDS7.BOOKED_TIME] = pd.Timestamp("2025-03-01 12:00")

    with caplog.at_level("WARNING"):
        cleaning.report_patients_with_multiple_accessions_same_day(df)
    assert "PAS0001" in caplog.text
