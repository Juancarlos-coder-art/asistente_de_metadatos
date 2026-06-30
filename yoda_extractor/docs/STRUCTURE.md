# Structure Extractor

Maps the dataset's column paths to predefined metadata fields using Gemini.
Returns **source columns** and, when needed, a **pandas transform** to derive a new column — never the values themselves.

## Output

Each field is an **array of mapping objects** — one per distinct column combination that satisfies it. Empty array `[]` means no mapping was found.

```json
{
  "structure_tmpt": {
    "number_of_unique_individuals": [
      {"columns": ["patient_id"], "transform": []}
    ],
    "min_typical_age": [],
    "max_typical_age": [],
    "temporal_coverage": [
      {"columns": ["event_date"], "transform": []}
    ],
    "errors": []
  }
}
```

## Mapping object structure

| Key | Type | Description |
|-----|------|-------------|
| `columns` | `string[]` | Source column paths involved in this mapping. |
| `transform` | `array` | List of DSL step dictionaries defining operations to perform sequentially on the columns, or `[]` when the field maps directly to the columns. |

---

## When is `transform` non-empty?

`transform` is provided when the field requires combining, parsing or converting columns. Supported DSL operators include:
- `to_string`: Casts a series to string with automated cleanups (e.g. converting `2017.0` to `"2017"`).
- `strip`: Strips leading and trailing whitespace.
- `split`: Splits a string on a separator and retrieves a specific index.
- `regex_extract`: Extracts a regex pattern with groups.
- `to_numeric`: Coerces a column to numeric, setting invalid values to NaN.
- `to_datetime_part`: Parses dates and extracts part (`"year"`, `"month"`, `"day"`).
- `replace`: Replaces text occurrences (supports regex).
- `map`: Mappings of keys to values (dictionaries).
- `json_extract`: Decodes a JSON-format column cell and extracts a value by key.
- `format_point`: Joins lat/lon values into a `"latitude,longitude"` format.
- `join_columns`: Combines multiple columns using a separator.
- `constant`: Injects a static value.

`transform` is `[]` when:
- The field maps directly to a single existing column (no combination needed).
- No columns were found for the field (`columns: []`).

---

## Fields mapped

| Field | Definition |
|-------|-----------|
| `number_of_unique_individuals` | Column(s) that identify a unique individual or entity (e.g. `patient_id`, `subject_id`) |
| `min_typical_age` | Column(s) containing the minimum age of the population |
| `max_typical_age` | Column(s) containing the maximum age of the population |
| `spatial` | Column(s) with geographic information (country, region, coordinates…) |
| `temporal_coverage` | Column(s) with date/time of data collection |
| `errors` | Array of error or ambiguity messages |

---

## How it works

### 1. Reservoir sampling (during streaming)

Up to 20 records sampled uniformly at random using Algorithm R (O(1) memory). See [`LLM.md`](LLM.md) for details.

### 2. Schema extraction (at result time)

All sampled records are recursively flattened into **dot-notation column paths** with up to 3 distinct example values each:

| Input record | Column path |
|--------------|-------------|
| `{"country": "ESP"}` | `country` |
| `{"patient": {"age": 30}}` | `patient.age` |
| `{"records": [{"date": "2020-01"}]}` | `records[].date` |

The schema (paths + examples) is what gets sent to Gemini — not the raw records — keeping the prompt compact even for deeply nested datasets.

### 3. Gemini call

The prompt includes:
- Filename (basename only)
- Number of columns and sampled records
- Full schema (sorted paths with example values)
- Instructions to return `columns` + `transform` (as a list of DSL step dictionaries) per field.

### 4. Response parsing

- Each field is normalised to a list of `{"columns": [...], "transform": [...]}` objects.
- A single mapping object (old format) is automatically wrapped in a list.
- Plain string column names are wrapped as `{"columns": [name], "transform": []}`.
- If JSON parsing fails entirely, all fields return `[]` and the error is reported.

---

## Architecture

`StructureExtractor` extends `BaseLLMExtractor` (`extractors/base_llm.py`), which provides reservoir sampling, sample serialisation, the Gemini call, and markdown fence stripping. `StructureExtractor` adds:

- `_flatten(record)` — recursive dot-notation path extractor
- `_build_schema()` — aggregates paths and sample values across all reservoir records
- Its own prompt template and `_parse_response`

---

## Edge cases

| Situation | Behaviour |
|-----------|-----------|
| No records in dataset | All fields `[]`, error reported |
| Empty schema (all values null/empty) | All fields `[]`, error reported |
| Single existing column, no combination | `[{"columns": ["col"], "transform": []}]` |
| Multiple columns need combining | `[{"columns": [...], "transform": [{"op": "...", "params": {...}}]}]` |
| Multiple independent combinations | Array with one object per combination |
| Gemini returns single object | Wrapped in a list automatically |
| LLM call fails | All fields `[]`, exception message in `errors` |
| `GEMINI_API_KEY` not set | All fields `[]`, error from `llm_utils` |
