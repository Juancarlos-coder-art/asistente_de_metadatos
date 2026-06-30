"""Tests for StaticExtractor.result() and finalize() using real temp files."""
import re

import pytest

from extractors.static import StaticExtractor


# ── result() — defaults when input_json is empty ─────────────────────────────

@pytest.fixture
def csv_file(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("name,age\nAlice,30\n")
    return str(f)


@pytest.fixture
def ext(csv_file):
    return StaticExtractor(file_path=csv_file, input_json={})


def test_update_is_noop(ext):
    ext.update({"any": "record"})


def test_result_issued_is_iso_timestamp(ext):
    out = ext.result()
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$", out["issued"])


def test_result_modified_is_iso_timestamp(ext):
    out = ext.result()
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$", out["modified"])


def test_result_default_theme(ext):
    out = ext.result()
    assert out["theme"] == ["http://publications.europa.eu/resource/authority/data-theme/HEAL"]


def test_result_default_legal_basis(ext):
    out = ext.result()
    assert out["legal_basis"]["description"] == "RGPD"


def test_result_default_applicable_legislation(ext):
    out = ext.result()
    assert out["applicable_legislation"][0]["label"] == "GDPR"


def test_result_format_from_extension(ext):
    out = ext.result()
    assert out["format"] == "csv"


def test_result_mimetype_detected(ext):
    out = ext.result()
    assert out.get("mimetype") == "text/csv"


def test_result_size_computed(ext):
    out = ext.result()
    assert isinstance(out["size"], int)
    assert out["size"] > 0


def test_result_hash_computed(ext):
    out = ext.result()
    assert "hash" in out
    assert len(out["hash"]) == 64
    assert out["hash_algorithm"] == "SHA-256"


def test_result_default_version(ext):
    out = ext.result()
    assert out["version"] == "1.0"


def test_result_default_has_version(ext):
    out = ext.result()
    assert out["has_version"] == ["1.0"]


# ── result() — prefilled fields are respected ─────────────────────────────────

def test_result_prefilled_issued(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"issued": "2023-01-01T00:00:00.000Z"})
    out = ext.result()
    assert out["issued"] == "2023-01-01T00:00:00.000Z"


def test_result_prefilled_modified(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"modified": "2024-06-01T00:00:00.000Z"})
    out = ext.result()
    assert out["modified"] == "2024-06-01T00:00:00.000Z"


def test_result_prefilled_theme(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"theme": ["custom-theme"]})
    out = ext.result()
    assert out["theme"] == ["custom-theme"]


def test_result_prefilled_mimetype(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"mimetype": "application/octet-stream"})
    out = ext.result()
    assert out["mimetype"] == "application/octet-stream"


def test_result_prefilled_format(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"format": "tsv"})
    out = ext.result()
    assert out["format"] == "tsv"


def test_result_prefilled_size(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"size": 9999})
    out = ext.result()
    assert out["size"] == 9999


def test_result_prefilled_hash(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"hash": "abc123", "hash_algorithm": "MD5"})
    out = ext.result()
    assert out["hash"] == "abc123"
    assert out["hash_algorithm"] == "MD5"


def test_result_prefilled_legal_basis(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"legal_basis": {"description": "Custom"}})
    out = ext.result()
    assert out["legal_basis"]["description"] == "Custom"


def test_result_prefilled_applicable_legislation(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"applicable_legislation": [{"uri": "custom"}]})
    out = ext.result()
    assert out["applicable_legislation"] == [{"uri": "custom"}]


# ── result() — version increment logic ───────────────────────────────────────

def test_result_version_incremented(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"version": "1.0"})
    out = ext.result()
    assert out["version"] == "2.0"


def test_result_version_non_parseable_kept_as_is(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"version": "draft"})
    out = ext.result()
    assert out["version"] == "draft"


def test_result_has_version_incremented(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"has_version": ["1.0", "2.0"]})
    out = ext.result()
    assert "3.0" in out["has_version"]


def test_result_has_version_empty_list_defaults(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"has_version": []})
    out = ext.result()
    assert out["has_version"] == ["1.0"]


def test_result_has_version_non_parseable_list_kept(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"has_version": ["draft", "v2"]})
    out = ext.result()
    assert out["has_version"] == ["draft", "v2"]


def test_result_has_version_non_list_kept_as_is(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"has_version": "2.0"})
    out = ext.result()
    assert out["has_version"] == "2.0"


# ── result() — no file extension / missing file ───────────────────────────────

def test_result_no_extension_no_format(tmp_path):
    f = tmp_path / "noext"
    f.write_text("data")
    ext = StaticExtractor(file_path=str(f), input_json={})
    out = ext.result()
    assert "format" not in out


def test_result_missing_file_no_size_no_hash():
    ext = StaticExtractor(file_path="/nonexistent/path/data.csv", input_json={})
    out = ext.result()
    assert "size" not in out
    assert "hash" not in out


# ── finalize() ────────────────────────────────────────────────────────────────

def test_finalize_description_from_notes_input(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"notes": "Some notes"})
    out = ext.finalize(results={}, df=None)
    assert out["description"] == "Some notes"


def test_finalize_description_from_llm_notes(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={})
    results = {"llm_metadata": {"notes": "LLM notes"}}
    out = ext.finalize(results=results, df=None)
    assert out["description"] == "LLM notes"


def test_finalize_description_skipped_when_prefilled(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"description": "Already set"})
    out = ext.finalize(results={"llm_metadata": {"notes": "LLM notes"}}, df=None)
    assert "description" not in out


def test_finalize_name_from_title_input(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"title": "My Dataset"})
    out = ext.finalize(results={}, df=None)
    assert out["name"] == "My Dataset"


def test_finalize_name_from_llm_title(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={})
    results = {"llm_metadata": {"title": "LLM Title"}}
    out = ext.finalize(results=results, df=None)
    assert out["name"] == "LLM Title"


def test_finalize_name_skipped_when_prefilled(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={"name": "Already set"})
    out = ext.finalize(results={"llm_metadata": {"title": "LLM Title"}}, df=None)
    assert "name" not in out


def test_finalize_returns_empty_when_no_notes_or_title(csv_file):
    ext = StaticExtractor(file_path=csv_file, input_json={})
    out = ext.finalize(results={}, df=None)
    assert out == {}
