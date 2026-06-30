import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from utils.logger import get_logger

load_dotenv(Path(__file__).parent.parent / ".env")

MODEL = "gemini-3.1-flash-lite"
log = get_logger(__name__)


def call_gemini(prompt: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set — add it to .env or export it")

    log.debug("LLM prompt (%d chars):\n%s\n%s", len(prompt), "─" * 60, prompt)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = response.text

    log.debug("LLM response (%d chars):\n%s", len(text), text)
    return text
