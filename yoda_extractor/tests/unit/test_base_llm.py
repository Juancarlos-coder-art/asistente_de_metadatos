"""Unit tests for BaseLLMExtractor (reservoir sampling, helpers, _strip_fences)."""
import json

import pytest

from extractors.base_llm import BaseLLMExtractor, SAMPLE_SIZE


class _ConcreteExtractor(BaseLLMExtractor):
    name = "test_llm"

    def result(self) -> dict:
        return {}


@pytest.fixture
def ext():
    return _ConcreteExtractor(file_path="data.csv", input_json={})


# ── constructor ───────────────────────────────────────────────────────────────

def test_initial_reservoir_is_empty(ext):
    assert ext._reservoir == []
    assert ext._count == 0


# ── update / reservoir sampling ───────────────────────────────────────────────

def test_update_adds_records_within_sample_size(ext):
    for i in range(5):
        ext.update({"id": i})
    assert len(ext._reservoir) == 5
    assert ext._count == 5


def test_update_fills_reservoir_up_to_sample_size(ext):
    for i in range(SAMPLE_SIZE):
        ext.update({"id": i})
    assert len(ext._reservoir) == SAMPLE_SIZE


def test_update_does_not_exceed_sample_size(ext):
    for i in range(SAMPLE_SIZE + 50):
        ext.update({"id": i})
    assert len(ext._reservoir) == SAMPLE_SIZE
    assert ext._count == SAMPLE_SIZE + 50


def test_update_reservoir_sampling_replaces_slot(monkeypatch, ext):
    for i in range(SAMPLE_SIZE):
        ext.update({"id": i})
    monkeypatch.setattr("secrets.SystemRandom.randrange", lambda self, n: 0)
    ext.update({"id": 999})
    assert ext._reservoir[0] == {"id": 999}


# ── _filename property ────────────────────────────────────────────────────────

def test_filename_returns_basename():
    ext = _ConcreteExtractor(file_path="/some/path/data.csv")
    assert ext._filename == "data.csv"


def test_filename_unknown_when_no_path():
    ext = _ConcreteExtractor(file_path="")
    assert ext._filename == "unknown"


# ── _build_sample_str ─────────────────────────────────────────────────────────

def test_build_sample_str_empty_reservoir(ext):
    assert ext._build_sample_str() == ""


def test_build_sample_str_joins_records(ext):
    ext._reservoir = [{"a": 1}, {"b": 2}]
    result = ext._build_sample_str()
    lines = result.split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"a": 1}


def test_build_sample_str_respects_max_chars():
    ext = _ConcreteExtractor()
    big_record = {"data": "x" * 10_000}
    ext._reservoir = [big_record] * 10
    result = ext._build_sample_str()
    assert len(result) <= 30_000 + 200


# ── _strip_fences ────────────────────────────────────────────────────────────

def test_strip_fences_no_fences():
    raw = '{"key": "value"}'
    assert BaseLLMExtractor._strip_fences(raw) == raw


def test_strip_fences_removes_json_code_block():
    raw = '```json\n{"key": "value"}\n```'
    result = BaseLLMExtractor._strip_fences(raw)
    assert result == '{"key": "value"}'


def test_strip_fences_removes_plain_code_block():
    raw = '```\n{"key": "value"}\n```'
    result = BaseLLMExtractor._strip_fences(raw)
    assert '{"key": "value"}' in result


def test_strip_fences_fixes_invalid_backslash():
    raw = '{"path": "C:\\\\Users\\\\test"}'
    result = BaseLLMExtractor._strip_fences(raw)
    assert result is not None


def test_strip_fences_preserves_valid_escapes():
    raw = '{"msg": "hello\\nworld"}'
    result = BaseLLMExtractor._strip_fences(raw)
    parsed = json.loads(result)
    assert parsed["msg"] == "hello\nworld"


def test_strip_fences_handles_unicode_escape():
    raw = '{"char": "\\u0041"}'
    result = BaseLLMExtractor._strip_fences(raw)
    parsed = json.loads(result)
    assert parsed["char"] == "A"


