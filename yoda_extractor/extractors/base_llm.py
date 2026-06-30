"""
Shared base for LLM-based extractors.

Handles reservoir sampling and the Gemini call so subclasses only need to
define the prompt and parse the response.
"""

import json
import secrets
from pathlib import Path

from .base import BaseExtractor
from utils.llm_utils import call_gemini
from utils.logger import get_logger

log = get_logger(__name__)

SAMPLE_SIZE = 20
MAX_CHARS = 30_000


class BaseLLMExtractor(BaseExtractor):

    def __init__(self, file_path: str = "", input_json: dict | None = None) -> None:
        super().__init__(file_path, input_json)
        self._reservoir: list[dict] = []
        self._count: int = 0

    # ── Streaming ──────────────────────────────────────────────────────────────

    def update(self, record: dict) -> None:
        self._count += 1
        if self._count <= SAMPLE_SIZE:
            self._reservoir.append(record)
        else:
            j = secrets.SystemRandom().randrange(self._count)
            if j < SAMPLE_SIZE:
                self._reservoir[j] = record
                log.debug("[%s] reservoir slot %d replaced at record %d", self.name, j, self._count)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @property
    def _filename(self) -> str:
        return Path(self.file_path).name if self.file_path else "unknown"

    def _build_sample_str(self) -> str:
        lines, total = [], 0
        for rec in self._reservoir:
            line = json.dumps(rec, ensure_ascii=False)
            if total + len(line) > MAX_CHARS:
                break
            lines.append(line)
            total += len(line)
        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> str:
        log.info("[%s] calling LLM (reservoir=%d records)", self.name, len(self._reservoir))
        return call_gemini(prompt)

    @staticmethod
    def _strip_fences(raw: str) -> str:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1].lstrip("json").strip() if len(parts) > 1 else cleaned
        
        # Fix invalid backslash escapes within JSON string literals
        import re
        def fix_string(match):
            s = match.group(0)
            chars = []
            i = 0
            n = len(s)
            while i < n:
                if s[i] == "\\":
                    if i + 1 < n:
                        next_char = s[i + 1]
                        if next_char in '"\\/bfnrt':
                            chars.append("\\" + next_char)
                            i += 2
                            continue
                        elif next_char == "u" and i + 5 < n:
                            if all(c in "0123456789abcdefABCDEF" for c in s[i+2:i+6]):
                                chars.append("\\" + s[i+1:i+6])
                                i += 6
                                continue
                    chars.append("\\\\")
                    i += 1
                else:
                    chars.append(s[i])
                    i += 1
            return "".join(chars)

        return re.sub(r'"(?:\\.|[^"])*"', fix_string, cleaned)
