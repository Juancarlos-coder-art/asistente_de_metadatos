"""Tests for utils/vector_store.py using mocks for lancedb and sentence_transformers."""
from unittest.mock import MagicMock, patch

import pytest

import utils.vector_store as vs


# ── entry_text (pure function, no mock needed) ────────────────────────────────

def test_entry_text_joins_all_values():
    entry = {"label": "Health", "description": "Dataset about health", "uri": "http://example.com"}
    result = vs.entry_text(entry)
    assert "Health" in result
    assert "Dataset about health" in result
    assert "http://example.com" not in result


def test_entry_text_skips_empty_values():
    entry = {"label": "Health", "empty": "", "none_val": None}
    result = vs.entry_text(entry)
    assert result == "Health"


def test_entry_text_flattens_list_values():
    entry = {"keywords": ["health", "data", "medicine"]}
    result = vs.entry_text(entry)
    assert "health" in result
    assert "data" in result
    assert "medicine" in result


def test_entry_text_empty_entry():
    assert vs.entry_text({}) == ""
    assert vs.entry_text({"uri": "http://x.com"}) == ""


# ── get_model (mocked) ────────────────────────────────────────────────────────



def test_get_model_returns_cached(monkeypatch):
    sentinel = MagicMock()
    vs._model = sentinel
    result = vs.get_model()
    assert result is sentinel
    vs._model = None


# ── embed / embed_one (mocked) ────────────────────────────────────────────────

def test_embed_returns_list_of_vectors():
    mock_model = MagicMock()
    import numpy as np
    mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    vs._model = mock_model
    result = vs.embed(["text1", "text2"])
    assert len(result) == 2
    assert isinstance(result[0], list)
    vs._model = None


def test_embed_one_returns_single_vector():
    mock_model = MagicMock()
    import numpy as np
    mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    vs._model = mock_model
    result = vs.embed_one("text")
    assert isinstance(result, list)
    assert len(result) == 3
    vs._model = None


# ── connect (mocked) ──────────────────────────────────────────────────────────


def test_connect_returns_cached():
    sentinel = MagicMock()
    vs._db = sentinel
    result = vs.connect()
    assert result is sentinel
    vs._db = None


# ── table_names (mocked) ──────────────────────────────────────────────────────

def test_table_names_returns_list():
    mock_db = MagicMock()
    mock_db.table_names.return_value = ["health_category", "dcat_type"]
    vs._db = mock_db
    result = vs.table_names()
    assert result == ["health_category", "dcat_type"]
    vs._db = None


# ── search (mocked) ───────────────────────────────────────────────────────────


def test_search_returns_empty_when_table_not_found():
    mock_db = MagicMock()
    mock_db.table_names.return_value = []
    vs._db = mock_db
    results = vs.search("nonexistent_feature", "query", limit=1)
    assert results == []
    vs._db = None
