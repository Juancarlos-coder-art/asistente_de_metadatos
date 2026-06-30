"""Tests for StructureExtractor and its helper functions."""
import json
from unittest.mock import patch

import pytest

from extractors.structure import (
    StructureExtractor,
    _flatten,
    _to_transform_list,
    _FIELDS,
)


# ── _flatten ──────────────────────────────────────────────────────────────────

def test_flatten_simple_record():
    record = {"name": "Alice", "age": 30}
    result = _flatten(record)
    assert result["name"] == ["Alice"]
    assert result["age"] == ["30"]


def test_flatten_nested_dict():
    record = {"patient": {"age": 30, "city": "Madrid"}}
    result = _flatten(record)
    assert "patient.age" in result
    assert "patient.city" in result


def test_flatten_list_of_dicts():
    record = {"items": [{"id": 1, "val": "x"}]}
    result = _flatten(record)
    assert "items[].id" in result


def test_flatten_list_of_scalars():
    record = {"tags": ["a", "b", "c"]}
    result = _flatten(record)
    assert "tags" in result
    assert result["tags"] == ["a"]


def test_flatten_none_value_skipped():
    record = {"name": "Alice", "empty": None}
    result = _flatten(record)
    assert "empty" not in result


def test_flatten_empty_string_skipped():
    record = {"name": "Alice", "blank": ""}
    result = _flatten(record)
    assert "blank" not in result


# ── _to_transform_list ────────────────────────────────────────────────────────

def test_to_transform_list_empty_input():
    assert _to_transform_list(None) == []
    assert _to_transform_list([]) == []
    assert _to_transform_list("") == []


def test_to_transform_list_valid_list():
    steps = [{"op": "strip", "params": {}}]
    assert _to_transform_list(steps) == steps


def test_to_transform_list_filters_invalid_items():
    steps = [{"op": "strip", "params": {}}, "not_a_dict", {"no_op": True}]
    result = _to_transform_list(steps)
    assert len(result) == 1
    assert result[0]["op"] == "strip"


def test_to_transform_list_single_dict():
    step = {"op": "to_numeric", "params": {}}
    assert _to_transform_list(step) == [step]


def test_to_transform_list_dict_without_op():
    assert _to_transform_list({"no_op_key": True}) == []


# ── result(): skip LLM when all prefilled ─────────────────────────────────────

def test_result_skips_llm_when_all_stats_prefilled():
    prefilled = {f: [{"columns": ["col"]}] for f in _FIELDS}
    ext = StructureExtractor(input_json=prefilled)
    with patch("extractors.base_llm.call_gemini") as mock:
        result = ext.result()
    mock.assert_not_called()
    assert result["errors"] == []


# ── result(): empty reservoir ─────────────────────────────────────────────────

def test_result_empty_reservoir_returns_empty():
    ext = StructureExtractor(input_json={})
    result = ext.result()
    assert result["errors"] == ["No records to sample"]
    for f in _FIELDS:
        assert result[f] == []


# ── result(): successful LLM call ────────────────────────────────────────────

def _valid_structure_response(**overrides) -> str:
    data = {f: [] for f in _FIELDS}
    data["number_of_unique_individuals"] = [{"columns": ["id"], "transform": []}]
    data["temporal_coverage"] = [{"year": {"column": "year", "transform": []}, "month": None, "day": None}]
    data["errors"] = []
    data.update(overrides)
    return json.dumps(data)


def test_result_calls_llm_and_parses():
    ext = StructureExtractor(file_path="data.csv", input_json={})
    ext._reservoir = [{"id": "1", "year": "2020"}]
    with patch("extractors.base_llm.call_gemini", return_value=_valid_structure_response()):
        result = ext.result()
    assert isinstance(result["number_of_unique_individuals"], list)
    assert result["errors"] == []


def test_result_llm_failure_returns_error():
    ext = StructureExtractor(input_json={})
    ext._reservoir = [{"id": "1"}]
    with patch("extractors.base_llm.call_gemini", side_effect=RuntimeError("boom")):
        result = ext.result()
    assert any("LLM call failed" in e for e in result["errors"])


# ── _parse_response ───────────────────────────────────────────────────────────

def test_parse_response_invalid_json():
    ext = StructureExtractor()
    result = ext._parse_response("not json {{{")
    assert any("Could not parse" in e for e in result["errors"])


def test_parse_response_normalises_field():
    ext = StructureExtractor()
    data = {f: [] for f in _FIELDS}
    data["number_of_unique_individuals"] = [{"columns": ["id"], "transform": []}]
    data["errors"] = []
    result = ext._parse_response(json.dumps(data))
    assert result["number_of_unique_individuals"] == [{"columns": ["id"], "transform": []}]


# ── _normalise_field ──────────────────────────────────────────────────────────

def test_normalise_field_empty():
    assert StructureExtractor._normalise_field([]) == []
    assert StructureExtractor._normalise_field(None) == []


def test_normalise_field_list_of_dicts():
    val = [{"columns": ["id"], "transform": []}]
    result = StructureExtractor._normalise_field(val)
    assert result[0]["columns"] == ["id"]


def test_normalise_field_list_of_strings():
    result = StructureExtractor._normalise_field(["col_a", "col_b"])
    assert result[0]["columns"] == ["col_a"]
    assert result[1]["columns"] == ["col_b"]


def test_normalise_field_single_dict():
    val = {"columns": ["id"], "transform": []}
    result = StructureExtractor._normalise_field(val)
    assert len(result) == 1
    assert result[0]["columns"] == ["id"]


def test_normalise_field_columns_as_string():
    val = [{"columns": "id", "transform": []}]
    result = StructureExtractor._normalise_field(val)
    assert result[0]["columns"] == ["id"]


# ── _normalise_date_field ─────────────────────────────────────────────────────

def test_normalise_date_field_empty():
    assert StructureExtractor._normalise_date_field([]) == []


def test_normalise_date_field_valid():
    val = [{"year": {"column": "year", "transform": []}, "month": None, "day": None}]
    result = StructureExtractor._normalise_date_field(val)
    assert len(result) == 1
    assert result[0]["year"]["column"] == "year"


def test_normalise_date_field_skips_non_dicts():
    result = StructureExtractor._normalise_date_field(["not_a_dict"])
    assert result == []


def test_normalise_date_field_single_object_wrapped():
    val = {"year": {"column": "year", "transform": []}, "month": None, "day": None}
    result = StructureExtractor._normalise_date_field(val)
    assert len(result) == 1


# ── _normalise_part ───────────────────────────────────────────────────────────

def test_normalise_part_none():
    assert StructureExtractor._normalise_part(None) is None
    assert StructureExtractor._normalise_part("") is None


def test_normalise_part_string():
    result = StructureExtractor._normalise_part("year_col")
    assert result == {"column": "year_col", "transform": []}


def test_normalise_part_dict():
    result = StructureExtractor._normalise_part({"column": "year", "transform": []})
    assert result["column"] == "year"


def test_normalise_part_dict_columns_list():
    result = StructureExtractor._normalise_part({"columns": ["year", "month"], "transform": []})
    assert result["column"] == "year"


def test_normalise_part_dict_no_column():
    assert StructureExtractor._normalise_part({"transform": []}) is None


# ── _build_schema ─────────────────────────────────────────────────────────────

def test_build_schema_from_reservoir():
    ext = StructureExtractor()
    ext._reservoir = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
    schema = ext._build_schema()
    assert "name" in schema
    assert "Alice" in schema["name"] or "Bob" in schema["name"]
