"""Tests for LLMExtractor using mocked call_gemini."""
import json
from unittest.mock import patch

import pytest

from extractors.llm import LLMExtractor, _FIELDS, _ARRAY_FIELDS


def _valid_llm_response(**overrides) -> str:
    data = {f: ([] if f in _ARRAY_FIELDS else "") for f in _FIELDS}
    data["title"] = "Dataset Title"
    data["notes"] = "Some description."
    data["keyword"] = ["health", "data"]
    data["language"] = ["SPA"]
    data["errors"] = []
    data.update(overrides)
    return json.dumps(data)


# ── all fields prefilled → skip LLM ──────────────────────────────────────────

def test_result_skips_llm_when_all_prefilled():
    prefilled = {f: (["x"] if f in _ARRAY_FIELDS else "x") for f in _FIELDS}
    ext = LLMExtractor(input_json=prefilled)
    with patch("extractors.base_llm.call_gemini") as mock:
        result = ext.result()
    mock.assert_not_called()
    assert result["errors"] == []


# ── empty reservoir → returns empty fields ────────────────────────────────────

def test_result_empty_reservoir_returns_empty_fields():
    ext = LLMExtractor(input_json={})
    result = ext.result()
    assert result["errors"] == ["No records to sample"]
    for f in _ARRAY_FIELDS:
        assert result[f] == []


# ── successful LLM call ───────────────────────────────────────────────────────


# ── LLM call failure ─────────────────────────────────────────────────────────

def test_result_llm_failure_returns_error():
    ext = LLMExtractor(input_json={})
    ext._reservoir = [{"col": "val"}]
    with patch("extractors.base_llm.call_gemini", side_effect=RuntimeError("API error")):
        result = ext.result()
    assert any("LLM call failed" in e for e in result["errors"])


# ── _parse_response ───────────────────────────────────────────────────────────

def test_parse_response_valid_json():
    ext = LLMExtractor()
    raw = _valid_llm_response()
    result = ext._parse_response(raw)
    assert result["title"] == "Dataset Title"


def test_parse_response_invalid_json_returns_error():
    ext = LLMExtractor()
    result = ext._parse_response("not valid json {{{")
    assert any("Could not parse" in e for e in result["errors"])


def test_parse_response_array_field_as_string_split():
    ext = LLMExtractor()
    data = {f: ([] if f in _ARRAY_FIELDS else "") for f in _FIELDS}
    data["keyword"] = "health;data;science"
    data["errors"] = []
    result = ext._parse_response(json.dumps(data))
    assert result["keyword"] == ["health", "data", "science"]


def test_parse_response_errors_not_list_wrapped():
    ext = LLMExtractor()
    data = {f: ([] if f in _ARRAY_FIELDS else "") for f in _FIELDS}
    data["errors"] = "some error string"
    result = ext._parse_response(json.dumps(data))
    assert isinstance(result["errors"], list)


def test_parse_response_array_field_invalid_type_becomes_empty():
    ext = LLMExtractor()
    data = {f: ([] if f in _ARRAY_FIELDS else "") for f in _FIELDS}
    data["keyword"] = 42
    data["errors"] = []
    result = ext._parse_response(json.dumps(data))
    assert result["keyword"] == []
