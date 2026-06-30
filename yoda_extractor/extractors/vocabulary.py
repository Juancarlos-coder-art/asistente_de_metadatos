"""
Vocabulary matcher.

For each controlled vocabulary defined in list_vocabularies.csv, finds the best
matching entries given the dataset's English metadata. The matching strategy is
chosen per vocabulary via the CSV column 'Metadata-Processed-By':

  - LLM : one LLM call passing the full vocabulary (title_en_tmpt, notes_en_tmpt, keyword_en_tmpt).
  - RAG : embed the dataset metadata (purpose_en_tmpt, title_en_tmpt, notes_en_tmpt, keyword_en_tmpt)
          and do a nearest-neighbour search against a precomputed LanceDB table
          (see controlled_vocabularies/build_vector_db.py).

The number of results returned per vocabulary is controlled by the 'top-n' column
in list_vocabularies.csv (defaults to 1 when absent). All vocabulary fields are
always returned as arrays of URIs.

For RAG, results are filtered to those whose distance is within RAG_DISTANCE_FACTOR
(default 1.5) of the best hit's distance, capped at top-n.
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

RAG_DISTANCE_FACTOR = 1.2

_URI_LABEL_FIELDS = {"coding_system"}

_LOCATIONS_PATH = _VOCABS_DIR / "vocabs" / "locations.json"
_EU_COUNTRY_BASE = "http://publications.europa.eu/resource/authority/country/"

_PROMPT_SPATIAL = """\
You are a geographic metadata extractor. Given the dataset information below, \
identify all geographic entities mentioned or implied.

Dataset:
- Spatial coverage description: {spatial_tmpt}
- Title: {title}
- Description: {notes}
- Keywords: {keywords}

Identify matches from each of these four levels (only include entries that \
genuinely appear in the dataset):

1. Autonomous communities (Spain) — pick from this exact list:
{autonomies}

2. Provinces (Spain) — pick from this exact list:
{provinces}

3. Continents — pick from this exact list:
{continents}

4. Countries — return ISO 3166-1 alpha-3 codes (e.g. "ESP", "FRA", "DEU"). \
Do not invent codes; only include countries clearly present in the dataset.

Rules:
- Return ONLY a valid JSON object, no markdown, no explanation.
- Each key is an array (may be empty []).
- For levels 1–3 use the exact string from the list above.
- For level 4 use 3-letter ISO codes in uppercase.

{{
  "autonomies": [],
  "provinces": [],
  "continents": [],
  "countries": []
}}"""

_PROMPT_SINGLE = """\
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

_PROMPT_MULTI = """\
You are a metadata classifier. Given the dataset description below, select up to \
{top_n} best matching entries from the controlled vocabulary provided.

Dataset:
- Title: {title}
- Description: {notes}
- Keywords: {keywords}

Controlled vocabulary ({name}):
{vocab}

Rules:
- Return ONLY a JSON array of codes of the best matching entries (e.g. ["PHDR", "MRMR"]).
- Include only entries that genuinely fit — fewer than {top_n} is fine.
- If nothing fits, return [].
- No explanation, no markdown, just the JSON array."""


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


def _parse_top_n(row: dict) -> int:
    try:
        return max(1, int(row.get("top-n", 1)))
    except (ValueError, TypeError):
        return 1


def _parse_multiple(row: dict) -> bool:
    return row.get("multiple_output", "false").strip().lower() == "true"


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

        vocab_rows = _read_csv()
        # Initialize all vocabulary features to ensure they are always in output
        for row in vocab_rows:
            feature = row.get("Feature", "")
            multiple = _parse_multiple(row)
            if feature:
                output[feature] = [] if multiple else ("" if feature == "dcat_type" else None)
        output["code_values"] = []

        for row in vocab_rows:
            name     = row.get("Name", "")
            base_url = row.get("URL", "").rstrip("/")
            feature  = row.get("Feature", "")
            mode     = row.get("Metadata-Processed-By", "").strip().upper()
            top_n    = _parse_top_n(row)
            multiple = _parse_multiple(row)
            if not feature:
                continue

            if feature in self.input_json:
                log.info("[%s] Feature '%s' already prefilled, skipping match.", self.name, feature)
                val = self.input_json[feature]
                if val is None or not self.has_content(val):
                    output[feature] = [] if multiple else ("" if feature == "dcat_type" else None)
                else:
                    if multiple:
                        output[feature] = val if isinstance(val, list) else [val]
                    else:
                        output[feature] = val[0] if isinstance(val, list) else val
                
                # Special handling for coding_system -> code_values prefill
                if feature == "coding_system":
                    if "code_values" in self.input_json:
                        cv_val = self.input_json["code_values"]
                        output["code_values"] = cv_val if isinstance(cv_val, list) else ([cv_val] if cv_val is not None else [])
                    elif val and not isinstance(val, list):
                        label = val.get("label") if isinstance(val, dict) else val.split("/")[-1]
                        output["code_values"] = [label] if label else []
                continue

            if feature == "spatial":
                self._match_spatial(llm_result, output, errors)
            elif mode == "RAG":
                self._match_rag(feature, name, top_n, multiple, llm_result, output, errors)
            else:
                self._match_llm(feature, name, base_url, top_n, multiple, llm_result, output, errors)

        if "code_values" in self.input_json and not output.get("code_values"):
            output["code_values"] = self.input_json["code_values"]

        if errors:
            output["_vocabulary_errors"] = errors

        return output

    def _match_llm(self, feature: str, name: str, base_url: str, top_n: int, multiple: bool,
                   llm_result: dict, output: dict, errors: list) -> None:
        """Pick the best vocabulary entries by asking the LLM directly."""
        title    = llm_result.get("title_en_tmpt") or llm_result.get("title", "")
        notes    = llm_result.get("notes_en_tmpt") or llm_result.get("notes", "")
        keywords = llm_result.get("keyword_en_tmpt") or llm_result.get("keyword", "")
        if not any([title, notes, keywords]):
            return
        if not base_url:
            return

        vocab = _load_vocab(feature)
        if not vocab:
            log.warning("Vocab JSON not found for feature '%s'", feature)
            errors.append(f"{feature}: vocab JSON not found")
            return

        log.info("Matching vocabulary (LLM, top-%d, multiple=%s): %s (%d entries)",
                 top_n, multiple, name, len(vocab))

        if not multiple:
            prompt = _PROMPT_SINGLE.format(
                title=title, notes=notes, keywords=keywords,
                name=name, vocab=_vocab_summary(vocab),
            )
            try:
                raw = _strip(call_gemini(prompt))
                log.debug("[%s] LLM returned code: %s", feature, raw)
                if raw and raw != "NONE" and raw in vocab:
                    uri = f"{base_url}/{raw}"
                    if feature in _URI_LABEL_FIELDS:
                        output[feature] = {"uri": uri, "label": raw}
                        if feature == "coding_system":
                            if "code_values" not in self.input_json or not self.has_content(self.input_json["code_values"]):
                                output["code_values"] = [raw]
                                log.debug("[code_values] derived from coding_system → %r", output["code_values"])
                    else:
                        output[feature] = uri
                    log.info("[%s] matched → %s", feature, output[feature])
                elif raw and raw != "NONE":
                    log.warning("[%s] LLM returned unknown code '%s'", feature, raw)
                    errors.append(f"{feature}: LLM returned unknown code '{raw}'")
                else:
                    log.info("[%s] no match (NONE)", feature)
            except Exception as exc:
                log.error("[%s] LLM call failed — %s", feature, exc)
                errors.append(f"{feature}: LLM call failed — {exc}")
        else:
            prompt = _PROMPT_MULTI.format(
                top_n=top_n, title=title, notes=notes, keywords=keywords,
                name=name, vocab=_vocab_summary(vocab),
            )
            try:
                raw = _strip(call_gemini(prompt))
                log.debug("[%s] LLM returned codes: %s", feature, raw)
                codes = json.loads(raw) if raw.startswith("[") else []
                if not isinstance(codes, list):
                    codes = []
                uris = [f"{base_url}/{c}" for c in codes if isinstance(c, str) and c.strip() in vocab]
                unknown = [c for c in codes if isinstance(c, str) and c.strip() and c.strip() not in vocab]
                if unknown:
                    log.warning("[%s] LLM returned unknown codes %s", feature, unknown)
                    errors.append(f"{feature}: LLM returned unknown codes {unknown}")
                output[feature] = uris
                if uris:
                    log.info("[%s] matched → %s", feature, uris)
                else:
                    log.info("[%s] no match", feature)
            except Exception as exc:
                log.error("[%s] LLM call failed — %s", feature, exc)
                errors.append(f"{feature}: LLM call failed — {exc}")

    def _match_spatial(self, llm_result: dict, output: dict, errors: list) -> None:
        """Resolve spatial URIs across four geographic levels using a single LLM call.

        Threshold cascade (most specific → least specific):
          provinces → autonomies → countries → continents
        If detected entries at a level exceed SPATIAL_THRESHOLD (10%) of the total
        available at that level, that level is skipped and the next one is used instead.
        Continents have no threshold — all matches are always included.
        """
        _THRESHOLD = 0.10
        _WORLD_COUNTRY_COUNT = 50  # for threshold calculation

        if not _LOCATIONS_PATH.exists():
            log.warning("[spatial] locations.json not found at %s", _LOCATIONS_PATH)
            errors.append("spatial: locations.json not found")
            return

        spatial_tmpt = llm_result.get("spatial_tmpt", "")
        title    = llm_result.get("title_en_tmpt") or llm_result.get("title", "")
        notes    = llm_result.get("notes_en_tmpt") or llm_result.get("notes", "")
        keywords = llm_result.get("keyword_en_tmpt") or llm_result.get("keyword", "")
        if not any([spatial_tmpt, title, notes, keywords]):
            return

        locations = json.loads(_LOCATIONS_PATH.read_text(encoding="utf-8"))
        autonomies_map = locations.get("autonomies", {})
        provinces_map  = locations.get("provinces", {})
        continents_map = locations.get("contients", {})  # note: typo in source file

        prompt = _PROMPT_SPATIAL.format(
            spatial_tmpt=spatial_tmpt,
            title=title, notes=notes, keywords=keywords,
            autonomies="\n".join(f"  - {k}" for k in autonomies_map),
            provinces="\n".join(f"  - {k}" for k in provinces_map),
            continents="\n".join(f"  - {k}" for k in continents_map),
        )

        try:
            raw = _strip(call_gemini(prompt))
            log.debug("[spatial] LLM raw response: %s", raw)
            data = json.loads(raw)
        except Exception as exc:
            log.error("[spatial] LLM call or parse failed — %s", exc)
            errors.append(f"spatial: LLM call failed — {exc}")
            return

        # Resolve each level independently
        province_hits  = [(n, provinces_map[n])  for n in data.get("provinces", [])  if n in provinces_map]
        autonomy_hits  = [(n, autonomies_map[n]) for n in data.get("autonomies", []) if n in autonomies_map]
        continent_hits = [(n, continents_map[n]) for n in data.get("continents", []) if n in continents_map]
        country_hits   = [
            (c, f"{_EU_COUNTRY_BASE}{c.upper()}")
            for c in data.get("countries", [])
            if isinstance(c, str) and len(c) == 3 and c.isalpha()
        ]

        for n, _ in province_hits:
            log.info("[spatial] province matched: %s", n)
        for n, _ in autonomy_hits:
            log.info("[spatial] autonomy matched: %s", n)
        for c, _ in country_hits:
            log.info("[spatial] country matched: %s", c)
        for n, _ in continent_hits:
            log.info("[spatial] continent matched: %s", n)

        # --- Threshold cascade ---
        uris: list[str] = []

        # Level 1: provinces
        province_ratio = len(province_hits) / len(provinces_map) if provinces_map else 0
        if province_hits and province_ratio > _THRESHOLD:
            log.info("[spatial] provinces exceed threshold (%.0f%% of %d) → cascading to autonomies",
                     province_ratio * 100, len(provinces_map))
            cascade = "autonomies"
        elif province_hits:
            uris.extend(uri for _, uri in province_hits)
            cascade = None
        else:
            cascade = None

        # Level 2: autonomies (included normally OR triggered by province cascade)
        autonomy_ratio = len(autonomy_hits) / len(autonomies_map) if autonomies_map else 0
        if autonomy_hits and autonomy_ratio > _THRESHOLD:
            log.info("[spatial] autonomies exceed threshold (%.0f%% of %d) → cascading to countries",
                     autonomy_ratio * 100, len(autonomies_map))
            if cascade == "autonomies":
                cascade = "countries"
        elif autonomy_hits or cascade == "autonomies":
            uris.extend(uri for _, uri in autonomy_hits)
            cascade = None

        # Level 3: countries (included normally OR triggered by autonomy cascade)
        country_ratio = len(country_hits) / _WORLD_COUNTRY_COUNT if country_hits else 0
        if country_hits and country_ratio > _THRESHOLD:
            log.info("[spatial] countries exceed threshold (%.0f%% of ~%d) → cascading to continents",
                     country_ratio * 100, _WORLD_COUNTRY_COUNT)
            if cascade in ("countries", None):
                cascade = "continents"
        elif country_hits or cascade == "countries":
            uris.extend(uri for _, uri in country_hits)
            cascade = None

        # Level 4: continents — no threshold, always include all matches
        # Also triggered if cascaded from countries
        if continent_hits or cascade == "continents":
            uris.extend(uri for _, uri in continent_hits)

        # Deduplicate preserving order
        seen: set[str] = set()
        result = [u for u in uris if not (u in seen or seen.add(u))]
        if not result:
            result = [f"{_EU_COUNTRY_BASE}ESP"]
            log.info("[spatial] no matches found, defaulting to ESP")
        output["spatial"] = result
        log.info("[spatial] resolved %d URIs", len(output["spatial"]))

    def _match_rag(self, feature: str, name: str, top_n: int, multiple: bool,
                   llm_result: dict, output: dict, errors: list) -> None:
        """Pick the best vocabulary entries by embedding similarity (LanceDB)."""
        fields = ("purpose_en_tmpt", "title_en_tmpt", "notes_en_tmpt", "keyword_en_tmpt")
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
            log.info("Matching vocabulary (RAG, top-%d): %s", top_n, name)
            hits = search(feature, query, limit=top_n)
            if not hits:
                errors.append(f"{feature}: no vector table — run build_vector_db.py")
                return

            best_distance = hits[0].get("_distance", 0) or 0
            threshold = best_distance * RAG_DISTANCE_FACTOR

            uris = []
            for hit in hits:
                dist = hit.get("_distance", 0) or 0
                if dist > threshold:
                    break
                uri = hit.get("uri", "")
                if uri:
                    uris.append(uri)
                    log.info("[%s] matched → %s (code=%s, distance=%.4f)",
                             feature, uri, hit.get("code"), dist)

            if not uris:
                log.info("[%s] no match above threshold", feature)
                return

            if multiple:
                output[feature] = uris
            else:
                output[feature] = uris[0]
        except Exception as exc:
            log.error("[%s] RAG search failed — %s", feature, exc)
            errors.append(f"{feature}: RAG search failed — {exc}")
