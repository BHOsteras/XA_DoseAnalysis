"""Tests for merging IDS7 and DoseTrack data."""

import pytest

from conftest import ACC_BIPLANE, ACC_NORMAL, ACC_ONLY_DT, ACC_ONLY_IDS7, ACC_SIEMENS
from xa_dose_analysis import cleaning, merging
from xa_dose_analysis.columns import DT, IDS7
from xa_dose_analysis.io import MissingColumnsError


@pytest.fixture
def cleaned(ids7_df, dt_df_clean):
    return cleaning.clean_all(ids7_df, dt_df_clean)


@pytest.fixture
def merged(cleaned):
    df_ids7, df_dt = cleaned
    return merging.merge_ids7_dt(df_ids7, df_dt)


def test_one_row_per_accession(merged):
    assert merged[DT.ACCESSION].is_unique


def test_only_matching_accessions_merged(merged):
    assert ACC_ONLY_IDS7 not in set(merged[DT.ACCESSION])
    assert ACC_ONLY_DT not in set(merged[DT.ACCESSION])
    assert {ACC_NORMAL, ACC_BIPLANE, ACC_SIEMENS} <= set(merged[DT.ACCESSION])


def test_descriptions_concatenated_sorted(merged):
    row = merged[merged[DT.ACCESSION] == ACC_NORMAL].iloc[0]
    assert row[IDS7.DESCRIPTION] == "RG Angio abdomen, RG Lever"


def test_biplane_doses_summed(merged):
    row = merged[merged[DT.ACCESSION] == ACC_BIPLANE].iloc[0]
    assert row[DT.DAP_TOTAL] == pytest.approx(8.0)  # 5.0 + 3.0 (one row per tube)
    assert row[DT.CAK_TOTAL] == pytest.approx(80.0)  # 50.0 + 30.0
    assert row[DT.FLUORO_ACQ_TIME] == pytest.approx(300.0)  # 200.0 + 100.0


def test_max_columns_take_max(merged):
    row = merged[merged[DT.ACCESSION] == ACC_BIPLANE].iloc[0]
    assert row[DT.DAP_MAX] == pytest.approx(6.0)
    assert row[DT.KVP_MAX] == pytest.approx(90.0)


def test_categorical_columns_take_first(merged):
    row = merged[merged[DT.ACCESSION] == ACC_BIPLANE].iloc[0]
    assert row[DT.PATIENT_AGE] == 8
    assert row[DT.PATIENT_SEX] == "F"
    assert row[DT.ROOM] == "LAB_A"


def test_optional_ids7_columns_included(merged):
    assert "Pasient" in merged.columns
    assert IDS7.SEX in merged.columns


def test_missing_optional_columns_are_skipped(cleaned):
    df_ids7, df_dt = cleaned
    merged = merging.merge_ids7_dt(df_ids7, df_dt.drop(columns=[DT.KVP_MAX]))
    assert DT.KVP_MAX not in merged.columns
    assert DT.DAP_TOTAL in merged.columns


def test_merge_requires_flag_columns(ids7_df, dt_df_clean):
    with pytest.raises(MissingColumnsError, match="Henvisning_i_dt"):
        merging.merge_ids7_dt(ids7_df, dt_df_clean)
