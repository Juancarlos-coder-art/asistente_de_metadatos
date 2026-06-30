"""
Structure extractor.

Asks Gemini to map the dataset's column paths to specific metadata fields.

Two output shapes:
  - Value fields (ages, ids, …): array of {columns, transform} objects, where
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
    "temporal_coverage",
)

# Date fields use a different mapping shape: an array of {year, month, day} objects,
# each part cleaned independently. They are joined and standardized later in temporal.py.
_DATE_FIELDS = ("temporal_coverage",)

_DATE_PARTS = ("year", "month", "day")

_EMPTY_FIELD: list = []


def _to_transform_list(raw: Any) -> list:
    """Normalise a transform value to a list of DSL step dictionaries."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict) and "op" in item]
    if isinstance(raw, dict) and "op" in raw:
        return [raw]
    return []

_PROMPT_TEMPLATE = """\
You are a dataset schema mapper.
Given the filename and the schema of a dataset (column paths with example values),
identify which column paths correspond to each metadata field.

Definitions:
- number_of_unique_individuals: column(s) that identify a unique individual/entity (e.g. patient_id, subject_id)
- min_typical_age: column(s) that contain the minimum age of the population
- max_typical_age: column(s) that contain the maximum age of the population
- temporal_coverage: column(s) with date/time information about when the data was collected

Fields fall into TWO groups with DIFFERENT output shapes.

GROUP A — value fields: number_of_unique_individuals, min_typical_age, max_typical_age.
Each is an ARRAY of mapping objects. Include one object per distinct combination of
columns that satisfies the field. Each object has two keys:
- "columns": array of source column path strings involved in this mapping
- "transform": an ORDERED ARRAY of transformation step objects (use [] if no transform is needed).
  Each step object in the "transform" array must have the shape:
    {{"op": "<op_name>", "params": {{ ... }}}}

GROUP B — date fields: temporal_coverage.
Each is an ARRAY of date-mapping objects. Each date-mapping has exactly three keys — "year", "month", "day" — and each key is either null (that part is absent) or an object:
  {{"column": "<source column path>", "transform": [ ... ]}}
Where "transform" is an ORDERED ARRAY of transformation step objects (use [] if no transform is needed).
Rules for date parts:
- CLEAN EACH PART ON ITS OWN. Do NOT combine year/month/day and do NOT parse the full date here — joining the parts into one column and parsing the date happens in a later step.
- Each part's "transform" cleans ONLY its single column. Do not try to assign to a specific column name; each step simply processes the previous step's output (or the raw column for the first step).
- A date field may still be an ARRAY with several date-mappings if different column sets independently express a date.

SUPPORTED TRANSFORMATION OPERATORS ("op"):
1. {{"op": "to_string", "params": {{}}}}
   Converts values to strings.
2. {{"op": "strip", "params": {{}}}}
   Removes leading and trailing whitespace.
3. {{"op": "split", "params": {{"sep": "<separator_or_regex>", "index": <integer_index>}}}}
   Splits the string using the separator (can be a character/string or regex) and selects the item at the specified 0-based index. (Use negative index like -1 to select from the end).
4. {{"op": "regex_extract", "params": {{"pattern": "<regex_pattern>", "group": <integer_group_index_default_0>}}}}
   Extracts a matching substring using regex. "group" is optional (default is 0).
5. {{"op": "to_numeric", "params": {{}}}}
   Converts strings/values to numbers (coercing errors to nulls/NaNs).
6. {{"op": "to_datetime_part", "params": {{"part": "year" | "month" | "day", "dayfirst": <boolean_default_false>}}}}
   Parses the date and extracts the requested part ("year", "month", or "day").
7. {{"op": "replace", "params": {{"old": "<old_value>", "new": "<new_value>", "regex": <boolean_default_false>}}}}
   Replaces occurrences of "old" with "new". If "regex" is true, treats "old" as a regular expression.
8. {{"op": "map", "params": {{"mapping": {{ ... }}}}}}
   Maps/replaces exact keys using a dictionary/object. For example: {{"mapping": {{"Otros": "España"}}}}
9. {{"op": "json_extract", "params": {{"key": "<json_key>", "filter_key": "<optional_filter_key>", "filter_val": "<optional_filter_value>"}}}}
   Parses the cell as JSON (safely, no eval) and extracts the value of "key" from the parsed dict/list. If it's a list, extracts the key from the first item, or the first item where filter_key == filter_val.
10. {{"op": "format_point", "params": {{"lat_col": "<latitude_column>", "lon_col": "<longitude_column>"}}}}
    Combines coordinate columns into a WKT point: "POINT(<lat> <lon>)" or similar format.
11. {{"op": "constant", "params": {{"value": "<constant_value>"}}}}
    Sets a constant value.

Robustness rules:
- NEVER use raw Python code strings or pandas expressions. Always use the JSON step-by-step format above.
- A single cell may hold MULTIPLE values (e.g. "May, June" or "April/May"). Use "split" to take the first token: {{"op": "split", "params": {{"sep": "[,/;-]", "index": 0}}}} followed by {{"op": "strip", "params": {{}}}}.
- Month columns may contain names ("April"), numbers (4) — clean to a consistent representation.
- Spanish/European numbers use '.' as thousands separator and ',' as decimal (e.g. "1.234,56"). Parse with "replace" operations before converting to numeric.

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
    name = "structure_tmpt"

    def result(self) -> dict[str, Any]:
        stats_fields = ("number_of_unique_individuals", "min_typical_age", "max_typical_age", "temporal_coverage")
        all_present = all(f in self.input_json for f in stats_fields)
        prefilled_stats = {
            f: self.input_json[f]
            for f in stats_fields
            if f in self.input_json and self.has_content(self.input_json[f])
        }
        if all_present or len(prefilled_stats) == len(stats_fields):
            log.info("[%s] All statistics fields present or prefilled in input_json, skipping schema mapping LLM call.", self.name)
            return {**{f: [] for f in _FIELDS}, "errors": []}

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
        """Rename df['<field>_mod'] → df['<field>_mod_1'] etc. (No-op in new DSL)."""
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
