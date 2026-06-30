import pandas as pd
import pytest

from utils.dsl_evaluator import evaluate_dsl


# ── evaluate_dsl edge cases ───────────────────────────────────────────────────

def test_returns_none_when_df_is_none():
    assert evaluate_dsl(None, {"columns": ["col"], "transform": []}) is None


def test_returns_none_when_no_columns():
    df = pd.DataFrame({"col": ["a"]})
    assert evaluate_dsl(df, {"columns": [], "transform": []}) is None


def test_returns_none_when_column_missing():
    df = pd.DataFrame({"col": ["a"]})
    assert evaluate_dsl(df, {"columns": ["nonexistent"], "transform": []}) is None


def test_uses_column_key_as_fallback():
    df = pd.DataFrame({"col": ["hello"]})
    result = evaluate_dsl(df, {"column": "col", "transform": []})
    assert result.iloc[0] == "hello"


def test_uses_initial_series_when_provided():
    df = pd.DataFrame({"col": ["x"]})
    series = pd.Series(["initial"])
    result = evaluate_dsl(df, {"columns": ["col"], "transform": []}, initial_series=series)
    assert result.iloc[0] == "initial"


def test_returns_none_on_failed_transform(simple_df):
    mapping = {
        "columns": ["name"],
        "transform": [{"op": "unknown_op_xyz", "params": {}}],
    }
    result = evaluate_dsl(simple_df, mapping)
    assert result is None


# ── op: to_string ─────────────────────────────────────────────────────────────

def test_to_string_strips_nan_like_values():
    df = pd.DataFrame({"col": [None, float("nan"), "nan", "none", ""]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_string", "params": {}}]})
    for val in result:
        assert val is None


def test_to_string_converts_float_int_to_plain_int():
    df = pd.DataFrame({"col": [1.0, 2.0, 3.5]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_string", "params": {}}]})
    assert result.iloc[0] == "1"
    assert result.iloc[1] == "2"
    assert result.iloc[2] == "3.5"


def test_to_string_keeps_regular_strings():
    df = pd.DataFrame({"col": ["hello", "world"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_string", "params": {}}]})
    assert result.iloc[0] == "hello"
    assert result.iloc[1] == "world"


# ── op: strip ────────────────────────────────────────────────────────────────

def test_strip_removes_whitespace():
    df = pd.DataFrame({"col": ["  hello  ", "\tworld\n", None]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "strip", "params": {}}]})
    assert result.iloc[0] == "hello"
    assert result.iloc[1] == "world"
    assert pd.isna(result.iloc[2])


# ── op: split ────────────────────────────────────────────────────────────────

def test_split_by_separator():
    df = pd.DataFrame({"col": ["a-b-c", "x-y", None]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "split", "params": {"sep": "-", "index": 1}}]})
    assert result.iloc[0] == "b"
    assert result.iloc[1] == "y"
    assert pd.isna(result.iloc[2])


def test_split_negative_index():
    df = pd.DataFrame({"col": ["a-b-c"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "split", "params": {"sep": "-", "index": -1}}]})
    assert result.iloc[0] == "c"


def test_split_out_of_range_returns_empty():
    df = pd.DataFrame({"col": ["a-b"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "split", "params": {"sep": "-", "index": 10}}]})
    assert result.iloc[0] == ""


# ── op: regex_extract ────────────────────────────────────────────────────────

def test_regex_extract_group_0():
    df = pd.DataFrame({"col": ["abc123def"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "regex_extract", "params": {"pattern": r"\d+", "group": 0}}]})
    assert result.iloc[0] == "123"


def test_regex_extract_no_match_returns_none():
    df = pd.DataFrame({"col": ["no digits here"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "regex_extract", "params": {"pattern": r"\d+", "group": 0}}]})
    assert result.iloc[0] is None


def test_regex_extract_null_input():
    df = pd.DataFrame({"col": [None]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "regex_extract", "params": {"pattern": r"\d+", "group": 0}}]})
    assert result.iloc[0] is None


# ── op: to_numeric ────────────────────────────────────────────────────────────

def test_to_numeric_converts_strings():
    df = pd.DataFrame({"col": ["10", "3.14", "bad"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_numeric", "params": {}}]})
    assert result.iloc[0] == 10
    assert result.iloc[1] == pytest.approx(3.14)
    assert pd.isna(result.iloc[2])


# ── op: to_datetime_part ─────────────────────────────────────────────────────

def test_to_datetime_part_year():
    df = pd.DataFrame({"col": ["2023-05-15", "invalid"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_datetime_part", "params": {"part": "year"}}]})
    assert result.iloc[0] == "2023"
    assert pd.isna(result.iloc[1])


def test_to_datetime_part_month():
    df = pd.DataFrame({"col": ["2023-05-15"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_datetime_part", "params": {"part": "month"}}]})
    assert result.iloc[0] == "5"


def test_to_datetime_part_day():
    df = pd.DataFrame({"col": ["2023-05-07"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_datetime_part", "params": {"part": "day"}}]})
    assert result.iloc[0] == "7"


def test_to_datetime_part_unknown_part_returns_original():
    df = pd.DataFrame({"col": ["2023-05-15"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_datetime_part", "params": {"part": "hour"}}]})
    assert result.iloc[0] == "2023-05-15"


# ── op: replace ───────────────────────────────────────────────────────────────

def test_replace_plain():
    df = pd.DataFrame({"col": ["hello world", None]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "replace", "params": {"old": "world", "new": "there", "regex": False}}]})
    assert result.iloc[0] == "hello there"
    assert pd.isna(result.iloc[1])


def test_replace_regex():
    df = pd.DataFrame({"col": ["abc123def456"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "replace", "params": {"old": r"\d+", "new": "X", "regex": True}}]})
    assert result.iloc[0] == "abcXdefX"


# ── op: map ───────────────────────────────────────────────────────────────────

def test_map_replaces_values():
    df = pd.DataFrame({"col": ["A", "B", "C"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "map", "params": {"mapping": {"A": "Alpha", "B": "Beta"}}}]})
    assert result.iloc[0] == "Alpha"
    assert result.iloc[1] == "Beta"
    assert result.iloc[2] == "C"


# ── op: json_extract ─────────────────────────────────────────────────────────

def test_json_extract_from_dict():
    df = pd.DataFrame({"col": ['{"name": "Madrid", "code": "ES30"}']})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "json_extract", "params": {"key": "name"}}]})
    assert result.iloc[0] == "Madrid"


def test_json_extract_from_list_first_element():
    df = pd.DataFrame({"col": ['[{"name": "Madrid"}, {"name": "Barcelona"}]']})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "json_extract", "params": {"key": "name"}}]})
    assert result.iloc[0] == "Madrid"


def test_json_extract_with_filter():
    df = pd.DataFrame({"col": ['[{"type": "city", "name": "Madrid"}, {"type": "region", "name": "CM"}]']})
    result = evaluate_dsl(df, {
        "columns": ["col"],
        "transform": [{"op": "json_extract", "params": {"key": "name", "filter_key": "type", "filter_val": "region"}}],
    })
    assert result.iloc[0] == "CM"


def test_json_extract_invalid_json_returns_none():
    df = pd.DataFrame({"col": ["not json at all"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "json_extract", "params": {"key": "name"}}]})
    assert result.iloc[0] is None


def test_json_extract_null_returns_none():
    df = pd.DataFrame({"col": [None]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "json_extract", "params": {"key": "name"}}]})
    assert result.iloc[0] is None


# ── op: format_point ─────────────────────────────────────────────────────────

def test_format_point_valid_coords():
    df = pd.DataFrame({"lat": [40.4, 41.3], "lon": [-3.7, 2.1]})
    result = evaluate_dsl(df, {"columns": ["lat"], "transform": [{"op": "format_point", "params": {"lat_col": "lat", "lon_col": "lon"}}]})
    assert result.iloc[0] == "POINT(40.4 -3.7)"
    assert result.iloc[1] == "POINT(41.3 2.1)"


def test_format_point_missing_lat_returns_empty():
    df = pd.DataFrame({"lat": [None, 41.3], "lon": [2.1, 2.1]})
    result = evaluate_dsl(df, {"columns": ["lat"], "transform": [{"op": "format_point", "params": {"lat_col": "lat", "lon_col": "lon"}}]})
    assert result.iloc[0] == ""


def test_format_point_missing_columns_returns_series():
    df = pd.DataFrame({"lat": [40.4]})
    result = evaluate_dsl(df, {"columns": ["lat"], "transform": [{"op": "format_point", "params": {"lat_col": "lat", "lon_col": "nonexistent"}}]})
    assert result.iloc[0] == 40.4


# ── op: join_columns ─────────────────────────────────────────────────────────

def test_join_columns_default_sep():
    df = pd.DataFrame({"a": ["foo"], "b": ["bar"]})
    result = evaluate_dsl(df, {"columns": ["a"], "transform": [{"op": "join_columns", "params": {"columns": ["a", "b"]}}]})
    assert result.iloc[0] == "foo, bar"


def test_join_columns_custom_sep():
    df = pd.DataFrame({"a": ["Gran Via"], "b": ["28013"]})
    result = evaluate_dsl(df, {"columns": ["a"], "transform": [{"op": "join_columns", "params": {"columns": ["a", "b"], "sep": " - "}}]})
    assert result.iloc[0] == "Gran Via - 28013"


def test_join_columns_no_valid_cols_returns_original():
    df = pd.DataFrame({"a": ["x"]})
    result = evaluate_dsl(df, {"columns": ["a"], "transform": [{"op": "join_columns", "params": {"columns": ["nope"]}}]})
    assert result.iloc[0] == "x"


# ── op: constant ─────────────────────────────────────────────────────────────

def test_constant_fills_series():
    df = pd.DataFrame({"col": ["a", "b", "c"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "constant", "params": {"value": "fixed"}}]})
    assert list(result) == ["fixed", "fixed", "fixed"]


# ── chained transforms ────────────────────────────────────────────────────────

def test_chained_strip_and_to_string():
    df = pd.DataFrame({"col": ["  hello  ", "  world  "]})
    result = evaluate_dsl(df, {
        "columns": ["col"],
        "transform": [
            {"op": "to_string", "params": {}},
            {"op": "strip", "params": {}},
        ],
    })
    assert result.iloc[0] == "hello"
    assert result.iloc[1] == "world"


# ── edge cases for specific branches ─────────────────────────────────────────

def test_non_dict_step_in_transforms_is_skipped():
    df = pd.DataFrame({"col": ["hello"]})
    result = evaluate_dsl(df, {
        "columns": ["col"],
        "transform": ["not_a_dict", {"op": "strip", "params": {}}],
    })
    assert result.iloc[0] == "hello"


def test_to_string_strips_dot_zero_suffix():
    df = pd.DataFrame({"col": ["5.0", "10.0", "3.14"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_string", "params": {}}]})
    assert result.iloc[0] == "5"
    assert result.iloc[1] == "10"
    assert result.iloc[2] == "3.14"


def test_to_string_bad_dot_zero_kept_as_is():
    df = pd.DataFrame({"col": ["bad.0"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "to_string", "params": {}}]})
    assert result.iloc[0] == "bad.0"


def test_split_exception_returns_empty():
    df = pd.DataFrame({"col": ["hello"]})
    # invalid regex pattern triggers exception in re.split
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "split", "params": {"sep": "[invalid", "index": 0}}]})
    assert result.iloc[0] == ""


def test_regex_extract_bad_group_returns_none():
    df = pd.DataFrame({"col": ["abc"]})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "regex_extract", "params": {"pattern": r"(abc)", "group": 99}}]})
    assert result.iloc[0] is None


def test_json_extract_list_with_non_dict_first_element():
    df = pd.DataFrame({"col": ['["just_a_string", "another"]']})
    result = evaluate_dsl(df, {"columns": ["col"], "transform": [{"op": "json_extract", "params": {"key": "name"}}]})
    assert result.iloc[0] is None
