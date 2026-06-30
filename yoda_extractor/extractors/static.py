"""
Static extractor.

Returns fields whose values are fixed at extraction time and require no
record inspection: issued and modified are both set to the current UTC
datetime in ISO-8601 format with millisecond precision.
"""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from .base import BaseExtractor
from utils.logger import get_logger
from utils.mime_types import get_mimetype

log = get_logger(__name__)


_LANGUAGE_BASE_URI = "http://publications.europa.eu/resource/authority/language/"


def _now_iso() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _expand_lang_code(lang: str) -> str:
    code = lang.strip().upper()
    if len(code) == 3 and code.isalpha():
        return f"{_LANGUAGE_BASE_URI}{code}"
    return lang.strip()


_ARRAY_FIELDS = {
    "purpose",
    "purpose_en_tmpt",
    "language",
    "keyword",
    "keyword_en_tmpt",
    "population_coverage",
    "health_category",
    "personal_data",
    "health_theme",
    "code_values",
    "was_generated_by",
    "spatial",
    "alternate_identifier",
    "is_referenced_by",
}
_SEMICOLON_FIELDS = {"keyword", "keyword_en_tmpt"}


def normalize_language(output: dict) -> dict:
    """Expand language codes to EU authority URIs. Handles both arrays and plain strings."""
    lang = output.get("language")
    if isinstance(lang, list):
        output["language"] = [_expand_lang_code(v) for v in lang if isinstance(v, str) and v.strip()]
    elif isinstance(lang, str) and lang.strip() and not lang.startswith("http"):
        output["language"] = [_expand_lang_code(lang)]
    elif isinstance(lang, str) and lang.strip():
        output["language"] = [lang.strip()]
    return output


def normalize_array_fields(output: dict) -> dict:
    """Ensure all fields that must be arrays are lists, coercing strings when needed."""
    output = normalize_language(output)
    for field in _ARRAY_FIELDS - {"language"}:
        val = output.get(field)
        if isinstance(val, list):
            pass
        elif isinstance(val, str) and val.strip():
            if field in _SEMICOLON_FIELDS:
                output[field] = [v.strip() for v in val.split(";") if v.strip()]
            else:
                output[field] = [val.strip()]
        elif field in output:
            output[field] = []
    return output


class StaticExtractor(BaseExtractor):
    name = "static"

    def update(self, record: dict) -> None:
        pass

    def result(self) -> dict[str, Any]:
        ts = _now_iso()
        out = {}
        if "issued" in self.input_json and self.has_content(self.input_json["issued"]):
            out["issued"] = self.input_json["issued"]
        else:
            out["issued"] = ts

        if "modified" in self.input_json and self.has_content(self.input_json["modified"]):
            out["modified"] = self.input_json["modified"]
        else:
            out["modified"] = ts

        if "theme" in self.input_json and self.has_content(self.input_json["theme"]):
            out["theme"] = self.input_json["theme"]
        else:
            out["theme"] = ["http://publications.europa.eu/resource/authority/data-theme/HEAL"]

        if "legal_basis" in self.input_json and self.has_content(self.input_json["legal_basis"]):
            out["legal_basis"] = self.input_json["legal_basis"]
        else:
            out["legal_basis"] = {
                "description": "RGPD",
                "source": "https://www.boe.es/doue/2016/119/L00001-00088.pdf",
            }

        p = Path(self.file_path)
        ext = p.suffix.lstrip(".").lower() or None

        if "mimetype" in self.input_json and self.has_content(self.input_json["mimetype"]):
            out["mimetype"] = self.input_json["mimetype"]
        else:
            detected = get_mimetype(self.file_path)
            if detected:
                out["mimetype"] = detected
                log.debug("[mimetype] detected from extension: %r → %r", self.file_path, detected)
            else:
                log.debug("[mimetype] unknown extension for: %r", self.file_path)

        if "format" in self.input_json and self.has_content(self.input_json["format"]):
            out["format"] = self.input_json["format"]
        elif ext:
            out["format"] = ext
            log.debug("[format] derived from extension: %r", ext)

        if "size" in self.input_json and self.has_content(self.input_json["size"]):
            out["size"] = self.input_json["size"]
        else:
            try:
                out["size"] = p.stat().st_size
                log.debug("[size] %d bytes", out["size"])
            except OSError as exc:
                log.debug("[size] could not stat file: %s", exc)

        if "hash" in self.input_json and self.has_content(self.input_json["hash"]):
            out["hash"] = self.input_json["hash"]
            out["hash_algorithm"] = self.input_json.get("hash_algorithm", "SHA-256")
        else:
            try:
                h = sha256()
                with open(p, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                out["hash"] = h.hexdigest()
                out["hash_algorithm"] = "SHA-256"
                log.debug("[hash] SHA-256: %s", out["hash"])
            except OSError as exc:
                log.debug("[hash] could not read file: %s", exc)

        if "applicable_legislation" in self.input_json and self.has_content(self.input_json["applicable_legislation"]):
            out["applicable_legislation"] = self.input_json["applicable_legislation"]
        else:
            out["applicable_legislation"] = [
                {
                    "uri": "http://data.europa.eu/eli/reg/2016/679/oj",
                    "label": "GDPR",
                },
                {
                    "uri": "http://data.europa.eu/eli/reg/2025/327/oj",
                    "label": "Reglamento EHDS",
                }
            ]

        raw_version = self.input_json.get("version")
        log.debug("[version] raw from input_json: %r", raw_version)
        if raw_version is None or not self.has_content(raw_version):
            out["version"] = "1.0"
            log.debug("[version] no input → defaulting to 1.0")
        else:
            try:
                new_version = f"{float(raw_version) + 1:.1f}"
                out["version"] = new_version
                log.debug("[version] incremented %r → %r", raw_version, new_version)
            except (ValueError, TypeError):
                out["version"] = raw_version
                log.debug("[version] could not parse %r, keeping as-is", raw_version)

        raw_has_version = self.input_json.get("has_version")
        log.debug("[has_version] raw from input_json: %r", raw_has_version)
        if raw_has_version is None or (isinstance(raw_has_version, list) and len(raw_has_version) == 0):
            out["has_version"] = ["1.0"]
            log.debug("[has_version] no input → defaulting to ['1.0']")
        elif isinstance(raw_has_version, list):
            try:
                nums = sorted(float(v) for v in raw_has_version)
                new_has_version = [f"{n:.1f}" for n in nums] + [f"{nums[-1] + 1:.1f}"]
                out["has_version"] = new_has_version
                log.debug("[has_version] %r → %r", raw_has_version, new_has_version)
            except (ValueError, TypeError):
                out["has_version"] = raw_has_version
                log.debug("[has_version] could not parse %r, keeping as-is", raw_has_version)
        else:
            out["has_version"] = raw_has_version
            log.debug("[has_version] non-list value %r, keeping as-is", raw_has_version)
        return out

    def finalize(self, results: dict, df: "Any") -> dict[str, Any]:
        out: dict[str, Any] = {}
        llm = results.get("llm_metadata", {})

        if "description" not in self.input_json or not self.has_content(self.input_json["description"]):
            notes = self.input_json.get("notes")
            if not self.has_content(notes):
                notes = llm.get("notes")
            if self.has_content(notes):
                log.debug("[description] derived from notes: %r", notes)
                out["description"] = notes

        if "name" not in self.input_json or not self.has_content(self.input_json["name"]):
            title = self.input_json.get("title")
            if not self.has_content(title):
                title = llm.get("title")
            if self.has_content(title):
                log.debug("[name] derived from title: %r", title)
                out["name"] = title

        return out
