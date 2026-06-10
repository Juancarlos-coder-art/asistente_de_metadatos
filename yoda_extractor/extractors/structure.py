"""
Structure extractor.

Asks Gemini to map the dataset's column paths to specific metadata fields.

Two output shapes:
  - Value fields (ages, ids, spatial, …): array of {columns, transform} objects, where
    transform is an ordered array of pandas snippets ([] if not needed).
  - Date fields (temporal_coverage): array of {year, month, day} objects.
    Each part is null or {column, transform} and is cleaned on its own. The parts are joined
    into a single column and standardized later in extractors/temporal.py.

Nested records are flattened to dot-notation paths:
  {"patient": {"age": 30}}    →  "patient.age"
  {"records": [{"date": ""}]} →  "records[].date"
"""

import json
from typing import Any

from .base_llm import BaseLLMExtractor
from utils.logger import get_logger

log = get_logger(__name__)

_FIELDS = (
    "number_of_unique_individuals",
    "min_typical_age",
    "max_typical_age",
    "spatial",
    "temporal_coverage",
)

# Date fields use a different mapping shape: an array of {year, month, day} objects,
# each part cleaned independently. They are joined and standardized later in temporal.py.
_DATE_FIELDS = ("temporal_coverage",)

_DATE_PARTS = ("year", "month", "day")

_EMPTY_FIELD: list = []


def _to_transform_list(raw: Any) -> list:
    """Normalise a transform value to a list of non-empty pandas-expression strings."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [s for s in raw if isinstance(s, str) and s.strip()]
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []

_PROMPT_TEMPLATE = """\
You are a dataset schema mapper.
Given the filename and the schema of a dataset (column paths with example values),
identify which column paths correspond to each metadata field.

Definitions:
- number_of_unique_individuals: column(s) that identify a unique individual/entity (e.g. patient_id, subject_id)
- min_typical_age: column(s) that contain the minimum age of the population
- max_typical_age: column(s) that contain the maximum age of the population
- spatial: column(s) with geographic information (country, region, coordinates, etc.)
- temporal_coverage: column(s) with date/time information about when the data was collected

Fields fall into TWO groups with DIFFERENT output shapes.

GROUP A — value fields: number_of_unique_individuals,
min_typical_age, max_typical_age, spatial.
Each is an ARRAY of mapping objects. Include one object per distinct combination of
columns that satisfies the field. Each object has two keys:
- "columns": array of source column path strings involved in this mapping
- "transform": an ORDERED ARRAY of single-line pandas expressions (use [] if no transform is needed).
  When multiple source columns are combined, list individual-column preparation steps first,
  then the final combination expression last. Every expression must assign to df['<field_name>_mod']
  (always plain _mod; numbering _mod_1, _mod_2 … is added automatically when there are several).
Include multiple mappings when different column combinations independently satisfy the same field
(e.g. both an ISO code column and a full-name column map to spatial).

GROUP B — date fields: temporal_coverage.
Each is an ARRAY of date-mapping objects. Each date-mapping has exactly three keys — "year",
"month", "day" — and each key is either null (that part is absent) or an object:
  {{"column": "<source column path>", "transform": [ ... ]}}
Rules for date parts:
- CLEAN EACH PART ON ITS OWN. Do NOT combine year/month/day and do NOT call pd.to_datetime here —
  joining the parts into one column and parsing the date happens in a later step.
- Each part's "transform" cleans ONLY its single column and assigns the cleaned values to
  df['<part>_<column>'] — e.g. df['year_Year'], df['month_Month'], df['day_Day'].
- Use [] for a part's transform when that raw column is already clean and needs no cleaning.
- A date field may still be an ARRAY with several date-mappings if different column sets
  independently express a date (e.g. a start-date triple and an end-date triple).
Example (year + month-name, no day):
  {{
    "year":  {{"column": "Year",  "transform": ["df['year_Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64').astype(str)"]}},
    "month": {{"column": "Month", "transform": ["df['month_Month'] = df['Month'].astype(str).str.split(r'[,/;-]').str[0].str.strip()"]}},
    "day":   null
  }}

Robustness rules (apply to every transform):
- NEVER use .astype(int) on a column that may contain NaN/blank/float values — it raises
  IntCastingNaNError and the whole transform fails. To turn a numeric year/month/day into a
  clean integer string use: pd.to_numeric(df['col'], errors='coerce').astype('Int64').astype(str)
  (the nullable 'Int64' drops the trailing '.0' and tolerates missing values).
- A single cell may hold MULTIPLE values (e.g. a Month column with "May, June" or "April, May, June").
  When sample values show commas/slashes/ranges, take the first token:
  df['col'].astype(str).str.split(r'[,/;-]').str[0].str.strip()
- Month columns may contain names ("April"), numbers (4), or be float — clean to a single
  consistent representation (a month name OR a number), never mixed.
- Spanish/European numbers use '.' as thousands separator and ',' as decimal (e.g. "1.234,56").
  Detect this from the sample values and parse with
  df['col'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float).
- Always prefer pd.to_numeric(df['col'], errors='coerce') over bare .astype(int).

Filename: {filename}
Schema ({n_cols} columns, from {n_records} sampled records):
{schema}

Return ONLY a valid JSON object — no markdown, no extra text.
Use an empty array [] for fields with no matching columns.
Add a message to errors for any ambiguity or problem encountered.

{{
  "number_of_unique_individuals": [],
  "min_typical_age": [],
  "max_typical_age": [],
  "spatial": [],
  "temporal_coverage": [],
  "errors": []
}}"""


def _flatten(record: Any, prefix: str = "") -> dict[str, list]:
    """Recursively flatten a record into dot-notation paths → [sample values]."""
    paths: dict[str, list] = {}
    if isinstance(record, dict):
        for key, val in record.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(val, dict):
                for k, v in _flatten(val, path).items():
                    paths.setdefault(k, []).extend(v)
            elif isinstance(val, list):
                if val and isinstance(val[0], dict):
                    for k, v in _flatten(val[0], f"{path}[]").items():
                        paths.setdefault(k, []).extend(v)
                else:
                    sample = str(val[0]) if val else ""
                    if sample:
                        paths.setdefault(path, []).append(sample)
            else:
                sample = str(val).strip() if val is not None else ""
                if sample:
                    paths.setdefault(path, []).append(sample)
    return paths


class StructureExtractor(BaseLLMExtractor):
    name = "structure"

    def result(self) -> dict[str, Any]:
        if not self._reservoir:
            return {**{f: [] for f in _FIELDS}, "errors": ["No records to sample"]}

        schema = self._build_schema()
        if not schema:
            return {**{f: [] for f in _FIELDS}, "errors": ["Could not extract schema from sample"]}

        schema_lines = []
        for path, samples in sorted(schema.items()):
            unique = list(dict.fromkeys(samples))[:3]
            schema_lines.append(f"  {path}: {unique}")

        prompt = _PROMPT_TEMPLATE.format(
            filename=self._filename,
            n_cols=len(schema),
            n_records=len(self._reservoir),
            schema="\n".join(schema_lines),
        )

        try:
            raw = self._call_llm(prompt)
            result = self._parse_response(raw)
            if result.get("errors"):
                log.warning("Structure errors: %s", result["errors"])
            else:
                log.info("Structure mapped %d columns", len(schema))
            return result
        except Exception as exc:
            log.error("Structure LLM call failed: %s", exc)
            return {**{f: [] for f in _FIELDS}, "errors": [f"LLM call failed: {exc}"]}

    def _build_schema(self) -> dict[str, list]:
        schema: dict[str, list] = {}
        for rec in self._reservoir:
            for path, values in _flatten(rec).items():
                schema.setdefault(path, []).extend(values)
        return schema

    def _parse_response(self, raw: str) -> dict:
        try:
            data = json.loads(self._strip_fences(raw))
        except json.JSONDecodeError as exc:
            return {**{f: [] for f in _FIELDS}, "errors": [f"Could not parse LLM response: {exc}"]}

        result = {}
        for f in _FIELDS:
            if f in _DATE_FIELDS:
                result[f] = self._normalise_date_field(data.get(f, []))
            else:
                mappings = self._normalise_field(data.get(f, []))
                result[f] = self._number_transforms(f, mappings)

        result["errors"] = data.get("errors", [])
        if not isinstance(result["errors"], list):
            result["errors"] = [str(result["errors"])]
        return result

    @staticmethod
    def _number_transforms(field: str, mappings: list) -> list:
        """Rename df['<field>_mod'] → df['<field>_mod_1'], df['<field>_mod_2'], … in each transform array."""
        idx = 0
        for mapping in mappings:
            if mapping["transform"]:
                idx += 1
                mapping["transform"] = [
                    expr.replace(f"df['{field}_mod']", f"df['{field}_mod_{idx}']")
                    for expr in mapping["transform"]
                ]
        return mappings

    @staticmethod
    def _normalise_field(val: Any) -> list:
        """Normalise any LLM response shape to a list of {columns, transform} objects.

        transform is always a list of strings (empty list means no transformation).
        """
        if not val:
            return []
        if isinstance(val, list):
            out = []
            for item in val:
                if isinstance(item, dict):
                    cols = item.get("columns", [])
                    out.append({
                        "columns": cols if isinstance(cols, list) else ([cols] if cols else []),
                        "transform": _to_transform_list(item.get("transform")),
                    })
                elif isinstance(item, str):
                    out.append({"columns": [item], "transform": []})
            return out
        if isinstance(val, dict):
            cols = val.get("columns", [])
            return [{"columns": cols if isinstance(cols, list) else ([cols] if cols else []),
                     "transform": _to_transform_list(val.get("transform"))}]
        return []

    @staticmethod
    def _normalise_date_field(val: Any) -> list:
        """Normalise a date field to a list of {year, month, day} mapping objects.

        Each part is either None or {"column": <str>, "transform": [<str>, ...]}.
        Tolerates the LLM returning a single object, a part as a bare column-name
        string, or columns/transform under slightly different keys.
        """
        items = val if isinstance(val, list) else ([val] if val else [])
        out = []
        for item in items:
            if not isinstance(item, dict):
                continue
            mapping = {part: StructureExtractor._normalise_part(item.get(part)) for part in _DATE_PARTS}
            if any(mapping.values()):
                out.append(mapping)
        return out

    @staticmethod
    def _normalise_part(raw: Any) -> dict | None:
        """Normalise one date part to {"column": <str>, "transform": [...]} or None."""
        if not raw:
            return None
        if isinstance(raw, str):
            return {"column": raw, "transform": []}
        if isinstance(raw, dict):
            col = raw.get("column", raw.get("columns"))
            if isinstance(col, list):
                col = col[0] if col else None
            if not col:
                return None
            return {"column": str(col), "transform": _to_transform_list(raw.get("transform"))}
        return None
