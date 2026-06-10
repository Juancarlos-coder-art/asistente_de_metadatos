# Structure Extractor

Maps the dataset's column paths to predefined metadata fields using Gemini.
Returns **source columns** and, when needed, a **pandas transform** to derive a new column — never the values themselves.

## Output

Each field is an **array of mapping objects** — one per distinct column combination that satisfies it. Empty array `[]` means no mapping was found.

```json
{
  "structure": {
    "number_of_unique_individuals": [
      {"columns": ["patient_id"], "transform": null}
    ],
    "min_typical_age": [],
    "max_typical_age": [],
    "spatial": [
      {"columns": ["country_code"], "transform": null},
      {"columns": ["lat", "lon"], "transform": "df['spatial_mod_1'] = df['lat'].astype(str) + ',' + df['lon'].astype(str)"}
    ],
    "temporal_coverage": [
      {"columns": ["event_date"], "transform": null}
    ],
    "errors": []
  }
}
```

## Mapping object structure

| Key | Type | Description |
|-----|------|-------------|
| `columns` | `string[]` | Source column paths involved in this mapping. |
| `transform` | `string \| null` | Single-line pandas expression that creates `df['<field>_mod']`, or `null` when the field maps directly to one existing column. |

When a field has multiple transforms they are automatically numbered: **`<field>_mod_1`**, **`<field>_mod_2`**, etc.
Fields with a single transform use `<field>_mod_1`. Fields with `transform: null` are not renamed.
Multiple mappings per field are included when different column combinations independently satisfy the same field.

---

## When is `transform` non-null?

`transform` is provided when the field requires combining or converting multiple columns:

| Situation | Example transform |
|-----------|------------------|
| Date split across year / month / day | `df['temporal_coverage_mod_1'] = pd.to_datetime(df[['year','month','day']])` |
| Full name from first + last | `df['number_of_unique_individuals_mod_1'] = df['first_name'].str.strip() + '_' + df['last_name'].str.strip()` |
| Coordinates from lat + lon | `df['spatial_mod_1'] = df['lat'].astype(str) + ',' + df['lon'].astype(str)` |
| Age derived from birth date | `df['min_typical_age_mod_1'] = (pd.Timestamp.now() - pd.to_datetime(df['birth_date'])).dt.days // 365` |

The LLM always writes `df['<field>_mod']`; the suffix `_1`, `_2`… is added automatically in code per transform order.

`transform` is `null` when:
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
- Instructions to return `columns` + `transform` per field, using `<field>_mod` as the new column name

### 4. Response parsing

- Each field is normalised to a list of `{"columns": [...], "transform": "..." | null}` objects.
- A single object (old format) is automatically wrapped in a list.
- Plain string column names are wrapped as `{"columns": [name], "transform": null}`.
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
| Single existing column, no combination | `[{"columns": ["col"], "transform": null}]` |
| Multiple columns need combining | `[{"columns": [...], "transform": "df['field_mod'] = ..."}]` |
| Multiple independent combinations | Array with one object per combination |
| Gemini returns single object | Wrapped in a list automatically |
| LLM call fails | All fields `[]`, exception message in `errors` |
| `GEMINI_API_KEY` not set | All fields `[]`, error from `llm_utils` |
