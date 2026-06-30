"""
Extension-to-IANA MIME type mapping loaded from mime.json (jshttp/mime-db).
"""

import json
from pathlib import Path

_MIME_JSON = Path(__file__).parent / "mime.json"

with open(_MIME_JSON, encoding="utf-8") as _f:
    MIME_TYPES: dict[str, str] = json.load(_f)


def get_mimetype(file_path: str) -> str | None:
    ext = Path(file_path).suffix.lstrip(".").lower()
    return MIME_TYPES.get(ext)
