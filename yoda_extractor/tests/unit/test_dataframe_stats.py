"""Unit tests for DataFrameStatisticsExtractor."""
import pandas as pd
import pytest

from extractors.dataframe_stats import DataFrameStatisticsExtractor, _resolve_series


# ── _resolve_series ───────────────────────────────────────────────────────────

def test_resolve_series_direct_column(simple_df):
    mapping = {"columns": ["age"]}
    result = _resolve_series(simple_df, mapping)
    assert list(result) == [30, 25, 40]


def test_resolve_series_missing_column(simple_df):
    mapping = {"columns": ["nonexistent"]}
    result = _resolve_series(simple_df, mapping)
    assert result is None


def test_resolve_series_empty_columns(simple_df):
    mapping = {"columns": []}
    result = _resolve_series(simple_df, mapping)
    assert result is None


def test_resolve_series_with_transform(simple_df):
    mapping = {
        "columns": ["name"],
        "transform": [{"op": "to_string", "params": {}}],
    }
    result = _resolve_series(simple_df, mapping)
    assert result is not None
    assert result.iloc[0] == "Alice"


def test_resolve_series_transform_failure_returns_none(simple_df):
    mapping = {
        "columns": ["name"],
        "transform": [{"op": "unknown_op", "params": {}}],
    }
    result = _resolve_series(simple_df, mapping)
    assert result is None


# ── _count_unique ─────────────────────────────────────────────────────────────

def test_count_unique_basic(simple_df):
    ext = DataFrameStatisticsExtractor()
    mappings = [{"columns": ["city"]}]
    result = ext._count_unique(simple_df, mappings)
    assert result == 3


def test_count_unique_with_duplicates():
    df = pd.DataFrame({"id": ["a", "b", "a", "c", "b"]})
    ext = DataFrameStatisticsExtractor()
    result = ext._count_unique(df, [{"columns": ["id"]}])
    assert result == 3


def test_count_unique_no_mappings(simple_df):
    ext = DataFrameStatisticsExtractor()
    assert ext._count_unique(simple_df, []) is None


def test_count_unique_invalid_column_tries_next(simple_df):
    ext = DataFrameStatisticsExtractor()
    mappings = [
        {"columns": ["nonexistent"]},
        {"columns": ["city"]},
    ]
    result = ext._count_unique(simple_df, mappings)
    assert result == 3


# ── _agg_numeric ──────────────────────────────────────────────────────────────

def test_agg_numeric_min(simple_df):
    ext = DataFrameStatisticsExtractor()
    result = ext._agg_numeric(simple_df, [{"columns": ["age"]}], "min")
    assert result == 25


def test_agg_numeric_max(simple_df):
    ext = DataFrameStatisticsExtractor()
    result = ext._agg_numeric(simple_df, [{"columns": ["age"]}], "max")
    assert result == 40


def test_agg_numeric_returns_int_when_whole_number():
    df = pd.DataFrame({"val": ["10", "20", "30"]})
    ext = DataFrameStatisticsExtractor()
    result = ext._agg_numeric(df, [{"columns": ["val"]}], "max")
    assert result == 30
    assert isinstance(result, int)


def test_agg_numeric_returns_float_when_decimal():
    df = pd.DataFrame({"val": ["10.5", "20.3"]})
    ext = DataFrameStatisticsExtractor()
    result = ext._agg_numeric(df, [{"columns": ["val"]}], "max")
    assert isinstance(result, float)


def test_agg_numeric_all_non_numeric_returns_none():
    df = pd.DataFrame({"val": ["a", "b", "c"]})
    ext = DataFrameStatisticsExtractor()
    result = ext._agg_numeric(df, [{"columns": ["val"]}], "min")
    assert result is None


def test_agg_numeric_no_mappings():
    df = pd.DataFrame({"val": [1, 2, 3]})
    ext = DataFrameStatisticsExtractor()
    assert ext._agg_numeric(df, [], "min") is None


# ── finalize / _extract ───────────────────────────────────────────────────────

def test_extract_number_of_records(simple_df):
    ext = DataFrameStatisticsExtractor()
    result = ext._extract(simple_df, {})
    assert result["number_of_records"] == 3


def test_extract_prefilled_number_of_records_is_respected(simple_df):
    ext = DataFrameStatisticsExtractor(input_json={"number_of_records": 999})
    result = ext._extract(simple_df, {})
    assert result["number_of_records"] == 999


def test_extract_unique_individuals(simple_df):
    ext = DataFrameStatisticsExtractor()
    structure = {"number_of_unique_individuals": [{"columns": ["name"]}]}
    result = ext._extract(simple_df, structure)
    assert result["number_of_unique_individuals"] == 2


def test_extract_min_max_age():
    df = pd.DataFrame({"age": ["18", "25", "65"]})
    ext = DataFrameStatisticsExtractor()
    structure = {
        "min_typical_age": [{"columns": ["age"]}],
        "max_typical_age": [{"columns": ["age"]}],
    }
    result = ext._extract(df, structure)
    assert result["min_typical_age"] == 18
    assert result["max_typical_age"] == 65


def test_finalize_no_df_returns_empty():
    ext = DataFrameStatisticsExtractor()
    result = ext.finalize(results={}, df=None)
    assert result == {}


def test_finalize_no_df_returns_prefilled():
    ext = DataFrameStatisticsExtractor(input_json={"number_of_records": 100})
    result = ext.finalize(results={}, df=None)
    assert result["number_of_records"] == 100


def test_finalize_with_df_runs_extract(simple_df):
    ext = DataFrameStatisticsExtractor()
    result = ext.finalize(results={"structure_tmpt": {}}, df=simple_df)
    assert result["number_of_records"] == 3


def test_result_returns_empty_dict():
    ext = DataFrameStatisticsExtractor()
    assert ext.result() == {}


def test_update_is_noop():
    ext = DataFrameStatisticsExtractor()
    ext.update({"key": "value"})


# ── prefilled field bypass in _extract ───────────────────────────────────────

def test_extract_prefilled_unique_individuals(simple_df):
    ext = DataFrameStatisticsExtractor(input_json={"number_of_unique_individuals": 42})
    result = ext._extract(simple_df, {})
    assert result["number_of_unique_individuals"] == 42


def test_extract_prefilled_min_age(simple_df):
    ext = DataFrameStatisticsExtractor(input_json={"min_typical_age": 5})
    result = ext._extract(simple_df, {})
    assert result["min_typical_age"] == 5


def test_extract_prefilled_max_age(simple_df):
    ext = DataFrameStatisticsExtractor(input_json={"max_typical_age": 99})
    result = ext._extract(simple_df, {})
    assert result["max_typical_age"] == 99


def test_extract_prefilled_temporal_coverage(simple_df):
    tc = {"start": "2020-01-01", "end": "2022-12-31"}
    ext = DataFrameStatisticsExtractor(input_json={"temporal_coverage": tc})
    result = ext._extract(simple_df, {})
    assert result["temporal_coverage"] == tc


# ── _resolve_series exception path ───────────────────────────────────────────

def test_resolve_series_dsl_exception_returns_none(simple_df):
    from unittest.mock import patch
    with patch("utils.dsl_evaluator.evaluate_dsl", side_effect=RuntimeError("boom")):
        mapping = {"columns": ["name"], "transform": [{"op": "strip", "params": {}}]}
        result = _resolve_series(simple_df, mapping)
    assert result is None


# ── _agg_numeric: series is None path ────────────────────────────────────────

def test_agg_numeric_invalid_then_valid_mapping():
    df = pd.DataFrame({"score": ["10", "20", "30"]})
    ext = DataFrameStatisticsExtractor()
    mappings = [
        {"columns": ["nonexistent"]},
        {"columns": ["score"]},
    ]
    result = ext._agg_numeric(df, mappings, "min")
    assert result == 10
