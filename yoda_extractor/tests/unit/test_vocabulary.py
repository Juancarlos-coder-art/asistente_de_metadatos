"""Tests for VocabularyMatcher using mocks."""
import json
from unittest.mock import MagicMock, patch

import pytest

from extractors.vocabulary import (
    VocabularyMatcher,
    _load_vocab,
    _parse_multiple,
    _parse_top_n,
    _strip,
    _vocab_summary,
)

_SAMPLE_VOCAB = {
    "PHDR": {"label": "Public health data registry", "uri": "http://example.com/PHDR"},
    "CLIN": {"label": "Clinical trial data", "uri": "http://example.com/CLIN"},
}

_SAMPLE_LLM_RESULT = {
    "title_en_tmpt": "Health registry",
    "notes_en_tmpt": "Registry of public health data",
    "keyword_en_tmpt": ["health", "registry"],
    "purpose_en_tmpt": ["research"],
    "spatial_tmpt": "Spain",
}


# ── helper functions ──────────────────────────────────────────────────────────

def test_strip_removes_whitespace_and_backticks():
    assert _strip("  `PHDR`  ") == "PHDR"
    assert _strip("  code  ") == "code"


def test_parse_top_n_default():
    assert _parse_top_n({}) == 1


def test_parse_top_n_valid():
    assert _parse_top_n({"top-n": "3"}) == 3


def test_parse_top_n_invalid_defaults_to_1():
    assert _parse_top_n({"top-n": "bad"}) == 1


def test_parse_top_n_zero_becomes_1():
    assert _parse_top_n({"top-n": "0"}) == 1


def test_parse_multiple_true():
    assert _parse_multiple({"multiple_output": "true"}) is True


def test_parse_multiple_false():
    assert _parse_multiple({"multiple_output": "false"}) is False


def test_parse_multiple_default_false():
    assert _parse_multiple({}) is False


def test_vocab_summary_excludes_uri():
    summary = _vocab_summary(_SAMPLE_VOCAB)
    assert "http://example.com" not in summary
    assert "PHDR" in summary


# ── update / result ───────────────────────────────────────────────────────────

def test_update_is_noop():
    ext = VocabularyMatcher()
    ext.update({"any": "record"})


def test_result_returns_empty_dict():
    ext = VocabularyMatcher()
    assert ext.result() == {}


# ── _match: prefilled feature bypass ─────────────────────────────────────────

def test_match_uses_prefilled_single_value():
    ext = VocabularyMatcher(input_json={"health_category": "http://example.com/X"})
    csv_rows = [{"Feature": "health_category", "Name": "Health", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "1", "multiple_output": "false"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert result["health_category"] == "http://example.com/X"


def test_match_uses_prefilled_multiple_value():
    ext = VocabularyMatcher(input_json={"health_category": ["http://example.com/A"]})
    csv_rows = [{"Feature": "health_category", "Name": "Health", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "3", "multiple_output": "true"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert result["health_category"] == ["http://example.com/A"]


# ── _match_llm: single result ─────────────────────────────────────────────────

def test_match_llm_single_returns_uri():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "health_category", "Name": "Health", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "1", "multiple_output": "false"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows), \
         patch("extractors.vocabulary._load_vocab", return_value=_SAMPLE_VOCAB), \
         patch("extractors.vocabulary.call_gemini", return_value="PHDR"):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert result["health_category"] == "http://example.com/PHDR"


def test_match_llm_single_none_no_output():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "health_category", "Name": "Health", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "1", "multiple_output": "false"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows), \
         patch("extractors.vocabulary._load_vocab", return_value=_SAMPLE_VOCAB), \
         patch("extractors.vocabulary.call_gemini", return_value="NONE"):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert result.get("health_category") is None


def test_match_llm_unknown_code_adds_error():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "health_category", "Name": "Health", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "1", "multiple_output": "false"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows), \
         patch("extractors.vocabulary._load_vocab", return_value=_SAMPLE_VOCAB), \
         patch("extractors.vocabulary.call_gemini", return_value="UNKNOWN_CODE"):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert "_vocabulary_errors" in result


def test_match_llm_failure_adds_error():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "health_category", "Name": "Health", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "1", "multiple_output": "false"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows), \
         patch("extractors.vocabulary._load_vocab", return_value=_SAMPLE_VOCAB), \
         patch("extractors.vocabulary.call_gemini", side_effect=RuntimeError("API error")):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert "_vocabulary_errors" in result


# ── _match_llm: multiple results ─────────────────────────────────────────────

def test_match_llm_multiple_returns_uri_list():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "dcat_type", "Name": "Type", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "3", "multiple_output": "true"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows), \
         patch("extractors.vocabulary._load_vocab", return_value=_SAMPLE_VOCAB), \
         patch("extractors.vocabulary.call_gemini", return_value='["PHDR", "CLIN"]'):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert result["dcat_type"] == ["http://example.com/PHDR", "http://example.com/CLIN"]


def test_match_llm_missing_vocab_json_adds_error():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "health_category", "Name": "Health", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "1", "multiple_output": "false"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows), \
         patch("extractors.vocabulary._load_vocab", return_value={}):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert "_vocabulary_errors" in result


def test_match_skips_feature_with_no_llm_metadata():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "health_category", "Name": "Health", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "1", "multiple_output": "false"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows), \
         patch("extractors.vocabulary._load_vocab", return_value=_SAMPLE_VOCAB), \
         patch("extractors.vocabulary.call_gemini") as mock_call:
        ext._match({})
    mock_call.assert_not_called()


# ── _match_rag ────────────────────────────────────────────────────────────────


def test_match_rag_multiple_hits_filtered_by_distance():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "health_theme", "Name": "Theme", "URL": "http://example.com",
                 "Metadata-Processed-By": "RAG", "top-n": "3", "multiple_output": "true"}]
    mock_hits = [
        {"uri": "http://example.com/A", "code": "A", "_distance": 0.1},
        {"uri": "http://example.com/B", "code": "B", "_distance": 0.11},
        {"uri": "http://example.com/C", "code": "C", "_distance": 0.9},
    ]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows), \
         patch("utils.vector_store.search", return_value=mock_hits):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert "http://example.com/A" in result["health_theme"]
    assert "http://example.com/C" not in result["health_theme"]


def test_match_skips_row_with_empty_feature():
    ext = VocabularyMatcher(input_json={})
    csv_rows = [{"Feature": "", "Name": "X", "URL": "http://example.com",
                 "Metadata-Processed-By": "LLM", "top-n": "1", "multiple_output": "false"}]
    with patch("extractors.vocabulary._read_csv", return_value=csv_rows):
        result = ext._match(_SAMPLE_LLM_RESULT)
    assert result == {"code_values": []}


# ── finalize ──────────────────────────────────────────────────────────────────

def test_finalize_calls_match_with_llm_metadata():
    ext = VocabularyMatcher(input_json={})
    results = {"llm_metadata": _SAMPLE_LLM_RESULT}
    with patch("extractors.vocabulary._read_csv", return_value=[]):
        result = ext.finalize(results=results, df=None)
    assert isinstance(result, dict)
