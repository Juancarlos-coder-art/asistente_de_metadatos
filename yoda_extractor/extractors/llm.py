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
           "purpose_en_tmpt", "title_en_tmpt", "notes_en_tmpt", "keyword_en_tmpt", "spatial_tmpt")

_ARRAY_FIELDS = {"purpose", "purpose_en_tmpt", "language", "keyword", "keyword_en_tmpt", "population_coverage"}

_PROMPT_TEMPLATE = """\
You are a metadata extractor for open datasets.
Given the filename and a sample of records, infer the following fields:

- language: Array of languages used inside the dataset (not the region of the data). Each as ISO 639-3 alpha-3 code (e.g. "ENG", "SPA", "FRA", "GLG", "CAT", "EUS"). Include all languages present. Must always be a JSON array (use [] if unknown).
- purpose: Array of purposes for which the data is collected/processed (free text). Content in Spanish. Must always be a JSON array (use [] if unknown).
- title: A concise title for the dataset. Content in Spanish.
- notes: A brief and narrative description of the dataset (2-4 sentences). Content in Spanish.
- keyword: Array of relevant keywords. Content in Spanish. Must always be a JSON array (use [] if unknown).
- population_coverage: Array of free-text descriptions of the population within the dataset. Content in Spanish. E.g.: ["Niños menores de 12 años con asma tratados en hospitales públicos de Francia entre 2018 y 2023."]. Must always be a JSON array (use [] if unknown).
- purpose_en_tmpt: Same as purpose but in English. Must always be a JSON array (use [] if unknown).
- title_en_tmpt: Same as title but in English.
- notes_en_tmpt: Same as notes but in English.
- keyword_en_tmpt: Same as keyword but in English. Must always be a JSON array (use [] if unknown).
- spatial_tmpt: A free-text description in English of the geographic coverage found in the sample records. Mention specific cities, countries,or continents that appear in the data values. Use "" if no geographic information is present or can be extracted.

Filename: {filename}
Sample ({n} records):
{sample}

Return ONLY a valid JSON object — no markdown, no extra text — with exactly these keys.
Set any string field you cannot determine to "" and array fields to [] and add a message to the errors array.

{{
  "purpose": ["..."],
  "language": ["..."],
  "title": "...",
  "notes": "...",
  "keyword": ["..."],
  "population_coverage": ["..."],
  "purpose_en_tmpt": ["..."],
  "title_en_tmpt": "...",
  "notes_en_tmpt": "...",
  "keyword_en_tmpt": ["..."],
  "spatial_tmpt": "...",
  "errors": []
}}"""


class LLMExtractor(BaseLLMExtractor):
    name = "llm_metadata"

    def result(self) -> dict[str, Any]:
        all_present = all(f in self.input_json for f in _FIELDS)
        prefilled = {
            f: self.input_json[f]
            for f in _FIELDS
            if f in self.input_json and self.has_content(self.input_json[f])
        }

        if all_present or len(prefilled) == len(_FIELDS):
            log.info("[%s] All fields present or prefilled in input_json, skipping LLM call.", self.name)
            res = {f: (self.input_json.get(f) if f in self.input_json else ([] if f in _ARRAY_FIELDS else "")) for f in _FIELDS}
            res["errors"] = []
            return res

        if not self._reservoir:
            res = {f: ([] if f in _ARRAY_FIELDS else "") for f in _FIELDS}
            res.update(prefilled)
            res["errors"] = ["No records to sample"]
            return res

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
            result.update(prefilled)
            return result
        except Exception as exc:
            log.error("LLM metadata call failed: %s", exc)
            res = {f: ([] if f in _ARRAY_FIELDS else "") for f in _FIELDS}
            res.update(prefilled)
            res["errors"] = [f"LLM call failed: {exc}"]
            return res

    def _parse_response(self, raw: str) -> dict:
        try:
            data = json.loads(self._strip_fences(raw))
        except json.JSONDecodeError as exc:
            result = {f: ([] if f in _ARRAY_FIELDS else "") for f in _FIELDS}
            result["errors"] = [f"Could not parse LLM response: {exc}"]
            return result

        result = {}
        for f in _FIELDS:
            if f in _ARRAY_FIELDS:
                val = data.get(f, [])
                if isinstance(val, list):
                    result[f] = [str(v).strip() for v in val if v]
                elif isinstance(val, str) and val.strip():
                    result[f] = [v.strip() for v in val.split(";") if v.strip()]
                else:
                    result[f] = []
            else:
                result[f] = str(data.get(f, "")).strip()
        result["errors"] = data.get("errors", [])
        if not isinstance(result["errors"], list):
            result["errors"] = [str(result["errors"])]
        return result
