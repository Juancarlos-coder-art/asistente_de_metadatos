import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from utils.logger import get_logger

# Hacer importable la raíz del proyecto para poder reutilizar assistant.llm_provider
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(_PROJECT_ROOT / ".env")

MODEL = "gemini-3.1-flash-lite"
GROQ_MODEL = os.getenv("YODA_GROQ_MODEL", "llama-3.3-70b-versatile")
log = get_logger(__name__)


def _use_groq() -> bool:
    """True si se debe usar Groq en lugar de Gemini (env YODA_LLM_BACKEND=groq)."""
    return os.getenv("YODA_LLM_BACKEND", "gemini").lower() in ("groq", "grok")


def _call_groq(prompt: str) -> str:
    """Backend alternativo: usa el cliente Groq compartido con la app principal."""
    from assistant.llm_provider import get_groq_client

    client = get_groq_client()
    if client is None:
        raise ValueError("GROQ_API_KEY not set — add it to .env or export it")

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


def call_gemini(prompt: str) -> str:
    log.debug("LLM prompt (%d chars):\n%s\n%s", len(prompt), "─" * 60, prompt)

    if _use_groq():
        log.debug("LLM backend: groq (model=%s)", GROQ_MODEL)
        text = _call_groq(prompt)
        log.debug("LLM response (%d chars):\n%s", len(text), text)
        return text

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set — add it to .env or export it")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = response.text

    log.debug("LLM response (%d chars):\n%s", len(text), text)
    return text
