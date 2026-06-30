"""Tests for utils/llm_utils.py using mocked google.genai."""
import os
from unittest.mock import MagicMock, patch

import pytest


def test_call_gemini_raises_when_no_api_key():
    from utils.llm_utils import call_gemini
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("GEMINI_API_KEY", None)
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            call_gemini("test prompt")


def test_call_gemini_returns_response_text():
    from utils.llm_utils import call_gemini
    mock_response = MagicMock()
    mock_response.text = "LLM response text"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
        with patch("utils.llm_utils.genai.Client", return_value=mock_client):
            result = call_gemini("test prompt")

    assert result == "LLM response text"
    mock_client.models.generate_content.assert_called_once()


