"""
Static extractor.

Returns fields whose values are fixed at extraction time and require no
record inspection: issued and modified are both set to the current UTC
datetime in ISO-8601 format with millisecond precision.
"""

from datetime import datetime, timezone
from typing import Any

from .base import BaseExtractor


_LANGUAGE_BASE_URI = "http://publications.europa.eu/resource/authority/language/"


def _now_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def normalize_language(output: dict) -> dict:
    """If 'language' is a bare 3-letter code, expand it to the EU authority URI."""
    lang = output.get("language", "")
    if isinstance(lang, str) and lang.strip() and not lang.startswith("http"):
        code = lang.strip().upper()
        if len(code) == 3 and code.isalpha():
            output["language"] = f"{_LANGUAGE_BASE_URI}{code}"
    return output


class StaticExtractor(BaseExtractor):
    name = "static"

    def update(self, record: dict) -> None:
        pass

    def result(self) -> dict[str, Any]:
        ts = _now_iso()
        return {"issued": ts, "modified": ts}
