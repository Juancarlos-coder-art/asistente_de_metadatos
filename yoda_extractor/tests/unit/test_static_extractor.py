import re

import pytest

from extractors.static import (
    _expand_lang_code,
    _now_iso,
    normalize_array_fields,
    normalize_language,
)

_LANGUAGE_BASE_URI = "http://publications.europa.eu/resource/authority/language/"


# ── _now_iso ──────────────────────────────────────────────────────────────────

def test_now_iso_format():
    ts = _now_iso()
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
    assert re.match(pattern, ts), f"Unexpected format: {ts!r}"


# ── _expand_lang_code ─────────────────────────────────────────────────────────

def test_expand_three_letter_alpha():
    assert _expand_lang_code("spa") == f"{_LANGUAGE_BASE_URI}SPA"
    assert _expand_lang_code("eng") == f"{_LANGUAGE_BASE_URI}ENG"


def test_expand_already_uppercase():
    assert _expand_lang_code("SPA") == f"{_LANGUAGE_BASE_URI}SPA"


def test_expand_short_code_not_three_letters():
    result = _expand_lang_code("es")
    assert result == "es"
    assert not result.startswith(_LANGUAGE_BASE_URI)


def test_expand_non_alpha_code():
    result = _expand_lang_code("es-419")
    assert result == "es-419".strip()


def test_expand_strips_whitespace():
    result = _expand_lang_code("  spa  ")
    assert result == f"{_LANGUAGE_BASE_URI}SPA"


# ── normalize_language ────────────────────────────────────────────────────────

def test_normalize_language_with_list():
    output = {"language": ["spa", "eng"]}
    result = normalize_language(output)
    assert result["language"] == [
        f"{_LANGUAGE_BASE_URI}SPA",
        f"{_LANGUAGE_BASE_URI}ENG",
    ]


def test_normalize_language_with_plain_string():
    output = {"language": "spa"}
    result = normalize_language(output)
    assert result["language"] == [f"{_LANGUAGE_BASE_URI}SPA"]


def test_normalize_language_already_uri_wraps_in_list():
    uri = f"{_LANGUAGE_BASE_URI}SPA"
    output = {"language": uri}
    result = normalize_language(output)
    assert result["language"] == [uri]


def test_normalize_language_empty_string_unchanged():
    output = {"language": ""}
    result = normalize_language(output)
    assert result["language"] == ""


def test_normalize_language_missing_key_unchanged():
    output = {"other": "value"}
    result = normalize_language(output)
    assert "language" not in result


def test_normalize_language_list_filters_empty():
    output = {"language": ["spa", "", "  "]}
    result = normalize_language(output)
    assert f"{_LANGUAGE_BASE_URI}SPA" in result["language"]
    assert len([v for v in result["language"] if not v.strip()]) == 0


# ── normalize_array_fields ────────────────────────────────────────────────────

def test_normalize_keyword_string_split_by_semicolon():
    output = {"keyword": "health; disease; data"}
    result = normalize_array_fields(output)
    assert result["keyword"] == ["health", "disease", "data"]


def test_normalize_keyword_already_list():
    output = {"keyword": ["health", "disease"]}
    result = normalize_array_fields(output)
    assert result["keyword"] == ["health", "disease"]


def test_normalize_purpose_plain_string_becomes_list():
    output = {"purpose": "research"}
    result = normalize_array_fields(output)
    assert result["purpose"] == ["research"]


def test_normalize_purpose_already_list():
    output = {"purpose": ["research", "education"]}
    result = normalize_array_fields(output)
    assert result["purpose"] == ["research", "education"]


def test_normalize_array_field_empty_value_becomes_empty_list():
    output = {"keyword": ""}
    result = normalize_array_fields(output)
    assert result["keyword"] == []


def test_normalize_population_coverage_plain_string():
    output = {"population_coverage": "national"}
    result = normalize_array_fields(output)
    assert result["population_coverage"] == ["national"]
