import pytest

from extractors.base import BaseExtractor


class _ConcreteExtractor(BaseExtractor):
    name = "test"

    def update(self, record: dict) -> None:
        pass

    def result(self) -> dict:
        return {}


@pytest.fixture
def extractor():
    return _ConcreteExtractor(file_path="test.csv", input_json={"key": "value"})


# ── has_content ───────────────────────────────────────────────────────────────

def test_has_content_none_is_false():
    assert BaseExtractor.has_content(None) is False


def test_has_content_empty_string_is_false():
    assert BaseExtractor.has_content("") is False


def test_has_content_whitespace_string_is_false():
    assert BaseExtractor.has_content("   ") is False


def test_has_content_non_empty_string_is_true():
    assert BaseExtractor.has_content("hello") is True


def test_has_content_empty_list_is_false():
    assert BaseExtractor.has_content([]) is False


def test_has_content_non_empty_list_is_true():
    assert BaseExtractor.has_content(["item"]) is True


def test_has_content_empty_dict_is_false():
    assert BaseExtractor.has_content({}) is False


def test_has_content_non_empty_dict_is_true():
    assert BaseExtractor.has_content({"key": "value"}) is True


def test_has_content_integer_is_true():
    assert BaseExtractor.has_content(0) is True
    assert BaseExtractor.has_content(42) is True


def test_has_content_float_is_true():
    assert BaseExtractor.has_content(0.0) is True
    assert BaseExtractor.has_content(3.14) is True


def test_has_content_boolean_is_true():
    assert BaseExtractor.has_content(False) is True
    assert BaseExtractor.has_content(True) is True


# ── constructor defaults ──────────────────────────────────────────────────────

def test_default_input_json_is_empty_dict():
    ext = _ConcreteExtractor()
    assert ext.input_json == {}


def test_default_file_path_is_empty():
    ext = _ConcreteExtractor()
    assert ext.file_path == ""


def test_constructor_stores_values(extractor):
    assert extractor.file_path == "test.csv"
    assert extractor.input_json == {"key": "value"}


# ── finalize default ──────────────────────────────────────────────────────────

def test_finalize_returns_empty_dict_by_default(extractor):
    result = extractor.finalize(results={}, df=None)
    assert result == {}
