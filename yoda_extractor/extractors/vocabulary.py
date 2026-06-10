"""
Vocabulary matcher.

For each controlled vocabulary defined in list_vocabularies.csv, finds the best
matching entry given the dataset's English metadata. The matching strategy is
chosen per vocabulary via the CSV column 'Metadata-Processed-By':

  - LLM : one LLM call passing the full vocabulary (title_en, notes_en, keyword_en).
  - RAG : embed the dataset metadata (purpose_en, title_en, notes_en, keyword_en)
          and do a nearest-neighbour search against a precomputed LanceDB table
          (see controlled_vocabularies/build_vector_db.py).

Returns {feature: full_uri} for every vocabulary row, or omits the field when the
vocab data is missing or no match is found.
"""

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .base import BaseExtractor
from utils.llm_utils import call_gemini
from utils.logger import get_logger

log = get_logger(__name__)

_VOCABS_DIR = Path(__file__).parent.parent / "controlled_vocabularies"
_CSV = _VOCABS_DIR / "list_vocabularies.csv"
_JSON_DIR = _VOCABS_DIR / "vocabs"

_PROMPT_TEMPLATE = """\
You are a metadata classifier. Given the dataset description below, select the \
single best matching entry from the controlled vocabulary provided.

Dataset:
- Title: {title}
- Description: {notes}
- Keywords: {keywords}

Controlled vocabulary ({name}):
{vocab}

Rules:
- Return ONLY the code of the best matching entry (e.g. "PHDR").
- If nothing fits, return "NONE".
- No explanation, no markdown, just the code."""


def _strip(text: str) -> str:
    return text.strip().strip("`").strip()


def _load_vocab(feature: str) -> dict:
    path = _JSON_DIR / f"{feature}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _vocab_summary(vocab: dict) -> str:
    stripped = {
        code: {k: v for k, v in entry.items() if k != "uri"}
        for code, entry in vocab.items()
    }
    return json.dumps(stripped, indent=2, ensure_ascii=False)


def _read_csv() -> list[dict]:
    rows = []
    with open(_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append({k.strip(): v.strip() for k, v in row.items() if k and k.strip()})
    return rows


class VocabularyMatcher(BaseExtractor):
    name = "vocabulary"

    def update(self, record: dict) -> None:
        pass

    def result(self) -> dict[str, Any]:
        return {}

    def finalize(self, results: dict, df: pd.DataFrame | None) -> dict[str, Any]:
        return self._match(results.get("llm_metadata", {}))

    def _match(self, llm_result: dict) -> dict[str, Any]:
        output: dict = {}
        errors: list = []

        for row in _read_csv():
            name     = row.get("Name", "")
            base_url = row.get("URL", "").rstrip("/")
            feature  = row.get("Feature", "")
            mode     = row.get("Metadata-Processed-By", "").strip().upper()
            if not feature:
                continue

            if mode == "RAG":
                self._match_rag(feature, name, llm_result, output, errors)
            else:
                self._match_llm(feature, name, base_url, llm_result, output, errors)

        if errors:
            output["_vocabulary_errors"] = errors

        return output

    def _match_llm(self, feature: str, name: str, base_url: str,
                   llm_result: dict, output: dict, errors: list) -> None:
        """Pick the best vocabulary entry by asking the LLM directly."""
        title    = llm_result.get("title_en") or llm_result.get("title", "")
        notes    = llm_result.get("notes_en") or llm_result.get("notes", "")
        keywords = llm_result.get("keyword_en") or llm_result.get("keyword", "")
        if not any([title, notes, keywords]):
            return
        if not base_url:
            return

        vocab = _load_vocab(feature)
        if not vocab:
            log.warning("Vocab JSON not found for feature '%s'", feature)
            errors.append(f"{feature}: vocab JSON not found")
            return

        log.info("Matching vocabulary (LLM): %s (%d entries)", name, len(vocab))
        prompt = _PROMPT_TEMPLATE.format(
            title=title, notes=notes, keywords=keywords,
            name=name, vocab=_vocab_summary(vocab),
        )

        try:
            raw = _strip(call_gemini(prompt))
            log.debug("[%s] LLM returned code: %s", feature, raw)
            if raw and raw != "NONE" and raw in vocab:
                output[feature] = f"{base_url}/{raw}"
                log.info("[%s] matched → %s", feature, output[feature])
            elif raw and raw != "NONE":
                log.warning("[%s] LLM returned unknown code '%s'", feature, raw)
                errors.append(f"{feature}: LLM returned unknown code '{raw}'")
            else:
                log.info("[%s] no match (NONE)", feature)
        except Exception as exc:
            log.error("[%s] LLM call failed — %s", feature, exc)
            errors.append(f"{feature}: LLM call failed — {exc}")

    def _match_rag(self, feature: str, name: str,
                   llm_result: dict, output: dict, errors: list) -> None:
        """Pick the best vocabulary entry by embedding similarity (LanceDB)."""
        fields = ("purpose_en", "title_en", "notes_en", "keyword_en")
        parts: list[str] = []
        for f in fields:
            value = llm_result.get(f) or llm_result.get(f.removesuffix("_en"))
            if not value:
                continue
            if isinstance(value, list):
                parts.extend(str(v) for v in value if v)
            else:
                parts.append(str(value))
        query = " ".join(p.strip() for p in parts if p.strip())
        if not query:
            return
        log.debug("[%s] RAG query text: %s", feature, query)

        try:
            from utils.vector_store import search
            log.info("Matching vocabulary (RAG): %s", name)
            hits = search(feature, query, limit=1)
            if not hits:
                errors.append(f"{feature}: no vector table — run build_vector_db.py")
                return
            hit = hits[0]
            uri = hit.get("uri", "")
            if uri:
                output[feature] = uri
                log.info("[%s] matched → %s (code=%s, distance=%.4f)",
                         feature, uri, hit.get("code"), hit.get("_distance", -1))
            else:
                log.info("[%s] nearest entry has no uri", feature)
        except Exception as exc:
            log.error("[%s] RAG search failed — %s", feature, exc)
            errors.append(f"{feature}: RAG search failed — {exc}")
