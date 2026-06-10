"""
LLM metadata extractor.

Uses Gemini to infer high-level metadata from the filename and a random sample
of up to 20 records (capped at 30 000 chars).
Requires the GEMINI_API_KEY environment variable.
"""

import json
from typing import Any

from .base_llm import BaseLLMExtractor
from utils.logger import get_logger

log = get_logger(__name__)

_FIELDS = ("purpose", "language", "title", "notes", "keyword", "population_coverage",
           "purpose_en", "title_en", "notes_en", "keyword_en")

_PROMPT_TEMPLATE = """\
You are a metadata extractor for open datasets.
Given the filename and a sample of records, infer the following fields:

- language: Language used inside the dataset not the region of the data. As ISO 639-3 alpha-3 code (e.g. "ENG", "SPA", "FRA", "GLG", "CAT", "EUS"). It is not necessary to be Spanish, sometimes it is the the cooficial codes of languages spoken in Spain (GLG, CAT, EUS)
- purpose: The purpose for which the data is collected/processed (free text). Content in Spanish.
- title: A concise title for the dataset. Content in Spanish.
- notes: A brief description (2-4 sentences). Content in Spanish.
- keyword: Relevant keywords separated by ";" with an space between them. Content in Spanish.
- population_coverage: A free-text description of the population within the dataset. Content in Spanish. E.g.: "Niños menores de 12 años con asma tratados en hospitales públicos de Francia entre 2018 y 2023." Or more generic if no specific population can be determined.
- purpose_en: Same as purpose but in English.
- title_en: Same as title but in English.
- notes_en: Same as notes but in English.
- keyword_en: Same as keyword but in English.

Filename: {filename}
Sample ({n} records):
{sample}

Return ONLY a valid JSON object — no markdown, no extra text — with exactly these keys.
Set any field you cannot determine to "" and add a message to the errors array.

{{
  "purpose": "...",
  "language": "...",
  "title": "...",
  "notes": "...",
  "keyword": "...",
  "population_coverage": "...",
  "purpose_en": "...",
  "title_en": "...",
  "notes_en": "...",
  "keyword_en": "...",
  "errors": []
}}"""


class LLMExtractor(BaseLLMExtractor):
    name = "llm_metadata"

    def result(self) -> dict[str, Any]:
        if not self._reservoir:
            return {**{f: "" for f in _FIELDS}, "errors": ["No records to sample"]}

        prompt = _PROMPT_TEMPLATE.format(
            filename=self._filename,
            n=len(self._reservoir),
            sample=self._build_sample_str(),
        )

        try:
            raw = self._call_llm(prompt)
            result = self._parse_response(raw)
            if result.get("errors"):
                log.warning("LLM metadata errors: %s", result["errors"])
            else:
                log.info("LLM metadata extracted: title=%r", result.get("title", ""))
            return result
        except Exception as exc:
            log.error("LLM metadata call failed: %s", exc)
            return {**{f: "" for f in _FIELDS}, "errors": [f"LLM call failed: {exc}"]}

    def _parse_response(self, raw: str) -> dict:
        try:
            data = json.loads(self._strip_fences(raw))
        except json.JSONDecodeError as exc:
            return {**{f: "" for f in _FIELDS}, "errors": [f"Could not parse LLM response: {exc}"]}

        result = {f: str(data.get(f, "")).strip() for f in _FIELDS}
        result["errors"] = data.get("errors", [])
        if not isinstance(result["errors"], list):
            result["errors"] = [str(result["errors"])]
        return result
