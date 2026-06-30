import pandas as pd
import pytest

from extractors.temporal import _as_str, _resolve_part, build_date_series, coverage


# ── _as_str ───────────────────────────────────────────────────────────────────

def test_as_str_replaces_missing_tokens():
    series = pd.Series(["2023", "nan", "none", "", "NaT", "<NA>"])
    result = _as_str(series, default="01")
    assert result.iloc[0] == "2023"
    for i in range(1, len(result)):
        assert result.iloc[i] == "01", f"index {i}: {result.iloc[i]!r}"


def test_as_str_strips_whitespace():
    series = pd.Series(["  2023  ", " 05 "])
    result = _as_str(series, default="01")
    assert result.iloc[0] == "2023"
    assert result.iloc[1] == "05"


# ── _resolve_part ─────────────────────────────────────────────────────────────

def test_resolve_part_none_returns_none():
    df = pd.DataFrame({"year": ["2023"]})
    assert _resolve_part(df, None) is None


def test_resolve_part_empty_dict_returns_none():
    df = pd.DataFrame({"year": ["2023"]})
    assert _resolve_part(df, {}) is None


def test_resolve_part_column_direct():
    df = pd.DataFrame({"year": ["2023", "2024"]})
    result = _resolve_part(df, {"column": "year"})
    assert list(result) == ["2023", "2024"]


def test_resolve_part_missing_column_returns_none():
    df = pd.DataFrame({"year": ["2023"]})
    assert _resolve_part(df, {"column": "nonexistent"}) is None


def test_resolve_part_with_transform():
    df = pd.DataFrame({"col": ["2023-05"]})
    part = {"column": "col", "columns": ["col"], "transform": [{"op": "split", "params": {"sep": "-", "index": 0}}]}
    result = _resolve_part(df, part)
    assert result.iloc[0] == "2023"


# ── build_date_series ─────────────────────────────────────────────────────────

def test_build_date_series_year_only(date_df):
    mapping = {"year": {"column": "year"}}
    result = build_date_series(date_df, mapping)
    assert result.iloc[0] == "2020-01-01"


def test_build_date_series_year_month(date_df):
    mapping = {
        "year": {"column": "year"},
        "month": {"column": "month"},
    }
    result = build_date_series(date_df, mapping)
    assert result.iloc[0] == "2020-01-01"
    assert result.iloc[1] == "2021-06-01"


def test_build_date_series_year_month_day(date_df):
    mapping = {
        "year": {"column": "year"},
        "month": {"column": "month"},
        "day": {"column": "day"},
    }
    result = build_date_series(date_df, mapping)
    assert result.iloc[0] == "2020-01-15"
    assert result.iloc[1] == "2021-06-30"
    assert result.iloc[2] == "2022-12-01"


def test_build_date_series_no_year_returns_none():
    df = pd.DataFrame({"month": ["05"], "day": ["15"]})
    mapping = {"month": {"column": "month"}, "day": {"column": "day"}}
    result = build_date_series(df, mapping)
    assert result is None


def test_build_date_series_missing_year_value_is_na():
    df = pd.DataFrame({"year": ["2020", None, "2022"]})
    mapping = {"year": {"column": "year"}}
    result = build_date_series(df, mapping)
    assert result.iloc[0] == "2020-01-01"
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == "2022-01-01"


# ── coverage ──────────────────────────────────────────────────────────────────

def test_coverage_returns_start_end(date_df):
    mappings = [{"year": {"column": "year"}, "month": {"column": "month"}, "day": {"column": "day"}}]
    result = coverage(date_df, mappings)
    assert result is not None
    assert result["start"] == "2020-01-15"
    assert result["end"] == "2022-12-01"


def test_coverage_returns_none_for_empty_mappings():
    df = pd.DataFrame({"year": ["2020"]})
    result = coverage(df, [])
    assert result is None


def test_coverage_returns_none_when_no_dates_parse():
    df = pd.DataFrame({"year": ["invalid"]})
    mappings = [{"year": {"column": "year"}}]
    result = coverage(df, mappings)
    assert result is None


def test_coverage_skips_non_dict_mappings():
    df = pd.DataFrame({"year": ["2020"]})
    result = coverage(df, ["not_a_dict", None])
    assert result is None


def test_coverage_multiple_mappings_uses_global_min_max():
    df = pd.DataFrame({"y1": ["2019", "2020"], "y2": ["2021", "2023"]})
    mappings = [
        {"year": {"column": "y1"}},
        {"year": {"column": "y2"}},
    ]
    result = coverage(df, mappings)
    assert result["start"] == "2019-01-01"
    assert result["end"] == "2023-01-01"
